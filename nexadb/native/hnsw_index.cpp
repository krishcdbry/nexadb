/*
 * NexaDB HNSW Index Implementation
 * =================================
 *
 * Custom HNSW (Hierarchical Navigable Small World) algorithm
 * - Optimized for batch insertion
 * - SIMD-optimized distance calculations
 * - Sub-millisecond search latency
 *
 * Reference: "Efficient and robust approximate nearest neighbor search
 * using Hierarchical Navigable Small World graphs" (Malkov & Yashunin, 2016)
 */

#include <vector>
#include <queue>
#include <unordered_set>
#include <unordered_map>
#include <random>
#include <cmath>
#include <algorithm>
#include <limits>

// Platform-specific SIMD headers
#if defined(__ARM_NEON) || defined(__aarch64__)
    #include <arm_neon.h>
#elif defined(__AVX2__)
    #include <immintrin.h>
#endif

namespace nexadb {
namespace native {

// Forward declare SIMD distance function
inline float l2_distance_simd(const float* a, const float* b, size_t dimensions);

/**
 * HNSW Index Node
 */
struct HNSWNode {
    size_t id;
    std::vector<std::vector<size_t>> neighbors;  // neighbors[layer] = list of neighbor IDs

    HNSWNode(size_t node_id, int max_layer)
        : id(node_id), neighbors(max_layer + 1) {}
};

/**
 * Priority queue element for search
 */
struct SearchCandidate {
    size_t id;
    float distance;

    bool operator<(const SearchCandidate& other) const {
        return distance < other.distance;  // Min-heap
    }

    bool operator>(const SearchCandidate& other) const {
        return distance > other.distance;  // Max-heap
    }
};

/**
 * HNSW Index
 * ==========
 *
 * Fast approximate nearest neighbor search
 * - Multi-layer graph structure
 * - Greedy search with backtracking
 * - SIMD-optimized distance calculations
 */
class HNSWIndex {
private:
    size_t dimensions_;
    size_t max_elements_;
    size_t num_vectors_;

    // HNSW parameters
    size_t M_;              // Number of connections per layer (default: 16)
    size_t M_max_;          // Max connections at layer 0 (default: M * 2)
    size_t ef_construction_; // Size of dynamic candidate list (default: 200)
    size_t ef_search_;      // Size of search candidate list (default: 100)
    double ml_;             // Normalization factor for level generation

    // Data storage
    std::vector<float> data_;  // Flat array of all vectors
    std::vector<HNSWNode> nodes_;  // Graph nodes
    size_t entry_point_;       // Entry point node ID
    int max_layer_;            // Maximum layer in the graph

    // Random number generator for layer assignment
    std::mt19937 rng_;
    std::uniform_real_distribution<double> level_dist_;

public:
    HNSWIndex(size_t dimensions, size_t max_elements = 1000000,
              size_t M = 16, size_t ef_construction = 200)
        : dimensions_(dimensions),
          max_elements_(max_elements),
          num_vectors_(0),
          M_(M),
          M_max_(M * 2),
          ef_construction_(ef_construction),
          ef_search_(100),
          ml_(1.0 / std::log(2.0 * M)),
          entry_point_(0),
          max_layer_(0),
          rng_(42),  // Fixed seed for reproducibility
          level_dist_(0.0, 1.0)
    {
        data_.reserve(max_elements * dimensions);
        nodes_.reserve(max_elements);
    }

    /**
     * Generate random level for new node
     */
    int get_random_level() {
        double r = level_dist_(rng_);
        return static_cast<int>(-std::log(r) * ml_);
    }

    /**
     * Calculate distance between two vectors
     */
    float distance(size_t id1, size_t id2) const {
        const float* v1 = &data_[id1 * dimensions_];
        const float* v2 = &data_[id2 * dimensions_];
        return l2_distance_simd(v1, v2, dimensions_);
    }

    /**
     * Calculate distance between vector and query
     */
    float distance_to_query(const float* query, size_t id) const {
        const float* v = &data_[id * dimensions_];
        return l2_distance_simd(query, v, dimensions_);
    }

    /**
     * Search for ef nearest neighbors at given layer
     */
    std::vector<SearchCandidate>
    search_layer(const float* query, size_t entry_id, size_t ef, int layer) const {
        std::unordered_set<size_t> visited;
        std::priority_queue<SearchCandidate, std::vector<SearchCandidate>, std::greater<SearchCandidate>> candidates;  // Min-heap
        std::priority_queue<SearchCandidate> W;  // Max-heap (result set)

        float d = distance_to_query(query, entry_id);
        candidates.push({entry_id, d});
        W.push({entry_id, d});
        visited.insert(entry_id);

        while (!candidates.empty()) {
            SearchCandidate c = candidates.top();
            candidates.pop();

            if (c.distance > W.top().distance) {
                break;  // All remaining candidates are farther
            }

            // Check neighbors
            const auto& neighbors = nodes_[c.id].neighbors[layer];
            for (size_t neighbor_id : neighbors) {
                if (visited.find(neighbor_id) == visited.end()) {
                    visited.insert(neighbor_id);

                    float d_neighbor = distance_to_query(query, neighbor_id);

                    if (d_neighbor < W.top().distance || W.size() < ef) {
                        candidates.push({neighbor_id, d_neighbor});
                        W.push({neighbor_id, d_neighbor});

                        if (W.size() > ef) {
                            W.pop();  // Remove furthest
                        }
                    }
                }
            }
        }

        // Convert priority queue to vector
        std::vector<SearchCandidate> results;
        while (!W.empty()) {
            results.push_back(W.top());
            W.pop();
        }
        std::reverse(results.begin(), results.end());  // Reverse to get ascending order
        return results;
    }

    /**
     * Add single vector to index
     */
    void add(const std::vector<float>& vector) {
        if (vector.size() != dimensions_) {
            throw std::invalid_argument("Vector dimension mismatch");
        }

        size_t new_id = num_vectors_;
        int new_level = get_random_level();

        // Store vector data
        data_.insert(data_.end(), vector.begin(), vector.end());

        // Create node
        nodes_.emplace_back(new_id, std::max(new_level, max_layer_));

        if (num_vectors_ == 0) {
            // First node - set as entry point
            entry_point_ = new_id;
            max_layer_ = new_level;
            num_vectors_++;
            return;
        }

        // Search for nearest neighbors
        size_t curr_nearest = entry_point_;

        // Find nearest at each layer above new_level
        for (int lc = max_layer_; lc > new_level; --lc) {
            auto nearest = search_layer(vector.data(), curr_nearest, 1, lc);
            if (!nearest.empty()) {
                curr_nearest = nearest[0].id;
            }
        }

        // Insert at each layer up to new_level
        for (int lc = std::min(new_level, max_layer_); lc >= 0; --lc) {
            auto candidates = search_layer(vector.data(), curr_nearest, ef_construction_, lc);

            size_t M = (lc == 0) ? M_max_ : M_;

            // Get M nearest neighbors
            std::vector<SearchCandidate> neighbors;
            for (size_t i = 0; i < M && i < candidates.size(); ++i) {
                neighbors.push_back(candidates[i]);
            }

            // Add bidirectional links
            for (const auto& neighbor : neighbors) {
                nodes_[new_id].neighbors[lc].push_back(neighbor.id);
                nodes_[neighbor.id].neighbors[lc].push_back(new_id);

                // Prune if needed
                if (nodes_[neighbor.id].neighbors[lc].size() > M) {
                    prune_connections(neighbor.id, lc, M);
                }
            }

            if (!neighbors.empty()) {
                curr_nearest = neighbors[0].id;
            }
        }

        // Update max layer if needed
        if (new_level > max_layer_) {
            max_layer_ = new_level;
            entry_point_ = new_id;
        }

        num_vectors_++;
    }

    /**
     * Prune connections to maintain M neighbors
     */
    void prune_connections(size_t node_id, int layer, size_t M) {
        auto& neighbors = nodes_[node_id].neighbors[layer];

        if (neighbors.size() <= M) {
            return;
        }

        // Calculate distances and sort
        std::vector<SearchCandidate> candidates;

        for (size_t neighbor_id : neighbors) {
            float d = distance(node_id, neighbor_id);
            candidates.push_back({neighbor_id, d});
        }

        std::sort(candidates.begin(), candidates.end());

        // Keep M nearest
        neighbors.clear();
        for (size_t i = 0; i < M && i < candidates.size(); ++i) {
            neighbors.push_back(candidates[i].id);
        }
    }

    /**
     * Batch add vectors (optimized)
     */
    void add_batch(const std::vector<std::vector<float>>& vectors) {
        for (const auto& vec : vectors) {
            add(vec);
        }
    }

    /**
     * Search for k nearest neighbors
     */
    std::vector<std::pair<size_t, float>> search(
        const std::vector<float>& query,
        size_t k
    ) {
        if (query.size() != dimensions_) {
            throw std::invalid_argument("Query dimension mismatch");
        }

        if (num_vectors_ == 0) {
            return {};
        }

        k = std::min(k, num_vectors_);

        // Find nearest at top layers
        size_t curr_nearest = entry_point_;
        for (int lc = max_layer_; lc > 0; --lc) {
            auto nearest = search_layer(query.data(), curr_nearest, 1, lc);
            if (!nearest.empty()) {
                curr_nearest = nearest[0].id;
            }
        }

        // Search at layer 0 with ef_search
        auto candidates = search_layer(query.data(), curr_nearest, std::max(ef_search_, k), 0);

        // Extract top k results
        std::vector<std::pair<size_t, float>> results;
        for (size_t i = 0; i < k && i < candidates.size(); ++i) {
            results.push_back({candidates[i].id, candidates[i].distance});
        }

        return results;
    }

    /**
     * Get number of vectors
     */
    size_t size() const {
        return num_vectors_;
    }

    /**
     * Get dimensions
     */
    size_t dimensions() const {
        return dimensions_;
    }

    /**
     * Clear all vectors
     */
    void clear() {
        data_.clear();
        nodes_.clear();
        num_vectors_ = 0;
        entry_point_ = 0;
        max_layer_ = 0;
    }

    /**
     * Set search parameters
     */
    void set_ef(size_t ef) {
        ef_search_ = ef;
    }
};

} // namespace native
} // namespace nexadb
