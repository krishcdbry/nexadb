/*
 * NexaDB Native Vector Operations
 * ================================
 *
 * High-performance vector operations using SIMD optimizations
 * - AVX2/AVX-512 for distance calculations
 * - Multi-threaded batch processing
 * - Memory-efficient storage
 *
 * Target: 50-100x faster than pure Python
 */

#include <vector>
#include <cmath>
#include <algorithm>
#include <limits>
#include <stdexcept>

// Platform-specific SIMD headers
#if defined(__ARM_NEON) || defined(__aarch64__)
    #include <arm_neon.h>  // ARM NEON for Apple Silicon / ARM
    #define HAVE_SIMD 1
#elif defined(__AVX2__)
    #include <immintrin.h>  // AVX2/AVX-512 for x86
    #define HAVE_SIMD 1
#else
    #define HAVE_SIMD 0
#endif

namespace nexadb {
namespace native {

/**
 * L2 distance calculation with SIMD optimization
 *
 * Calculates squared Euclidean distance between two vectors
 * - Uses ARM NEON on Apple Silicon (4x parallel)
 * - Uses AVX2 on x86 (8x parallel)
 * - Falls back to scalar on other platforms
 */
inline float l2_distance_simd(const float* a, const float* b, size_t dimensions) {
    float result = 0.0f;

#if defined(__ARM_NEON) || defined(__aarch64__)
    // ARM NEON path: Process 4 floats at a time
    size_t simd_size = dimensions - (dimensions % 4);
    float32x4_t sum = vdupq_n_f32(0.0f);

    for (size_t i = 0; i < simd_size; i += 4) {
        float32x4_t va = vld1q_f32(&a[i]);
        float32x4_t vb = vld1q_f32(&b[i]);
        float32x4_t diff = vsubq_f32(va, vb);
        sum = vmlaq_f32(sum, diff, diff);  // sum += diff * diff
    }

    // Horizontal sum of 4 floats
    float temp[4];
    vst1q_f32(temp, sum);
    result = temp[0] + temp[1] + temp[2] + temp[3];

    // Process remaining elements
    for (size_t i = simd_size; i < dimensions; ++i) {
        float diff = a[i] - b[i];
        result += diff * diff;
    }

#elif defined(__AVX2__)
    // AVX2 path: Process 8 floats at a time
    size_t simd_size = dimensions - (dimensions % 8);
    __m256 sum = _mm256_setzero_ps();

    for (size_t i = 0; i < simd_size; i += 8) {
        __m256 va = _mm256_loadu_ps(&a[i]);
        __m256 vb = _mm256_loadu_ps(&b[i]);
        __m256 diff = _mm256_sub_ps(va, vb);
        sum = _mm256_add_ps(sum, _mm256_mul_ps(diff, diff));
    }

    // Horizontal sum of 8 floats
    float temp[8];
    _mm256_storeu_ps(temp, sum);
    result = temp[0] + temp[1] + temp[2] + temp[3] +
             temp[4] + temp[5] + temp[6] + temp[7];

    // Process remaining elements
    for (size_t i = simd_size; i < dimensions; ++i) {
        float diff = a[i] - b[i];
        result += diff * diff;
    }

#else
    // Fallback: Scalar implementation
    for (size_t i = 0; i < dimensions; ++i) {
        float diff = a[i] - b[i];
        result += diff * diff;
    }
#endif

    return result;
}

/**
 * Cosine similarity with SIMD optimization
 *
 * - Uses ARM NEON on Apple Silicon
 * - Uses AVX2 on x86
 * - Falls back to scalar on other platforms
 */
inline float cosine_similarity_simd(const float* a, const float* b, size_t dimensions) {
    float dot_product = 0.0f;
    float norm_a = 0.0f;
    float norm_b = 0.0f;

#if defined(__ARM_NEON) || defined(__aarch64__)
    // ARM NEON path: Process 4 floats at a time
    size_t simd_size = dimensions - (dimensions % 4);
    float32x4_t dot_sum = vdupq_n_f32(0.0f);
    float32x4_t norm_a_sum = vdupq_n_f32(0.0f);
    float32x4_t norm_b_sum = vdupq_n_f32(0.0f);

    for (size_t i = 0; i < simd_size; i += 4) {
        float32x4_t va = vld1q_f32(&a[i]);
        float32x4_t vb = vld1q_f32(&b[i]);

        dot_sum = vmlaq_f32(dot_sum, va, vb);      // dot_sum += a * b
        norm_a_sum = vmlaq_f32(norm_a_sum, va, va); // norm_a += a * a
        norm_b_sum = vmlaq_f32(norm_b_sum, vb, vb); // norm_b += b * b
    }

    // Horizontal sum
    float temp_dot[4], temp_a[4], temp_b[4];
    vst1q_f32(temp_dot, dot_sum);
    vst1q_f32(temp_a, norm_a_sum);
    vst1q_f32(temp_b, norm_b_sum);

    for (int i = 0; i < 4; ++i) {
        dot_product += temp_dot[i];
        norm_a += temp_a[i];
        norm_b += temp_b[i];
    }

    // Process remaining elements
    for (size_t i = simd_size; i < dimensions; ++i) {
        dot_product += a[i] * b[i];
        norm_a += a[i] * a[i];
        norm_b += b[i] * b[i];
    }

#elif defined(__AVX2__)
    // AVX2 path: Process 8 floats at a time
    size_t simd_size = dimensions - (dimensions % 8);
    __m256 dot_sum = _mm256_setzero_ps();
    __m256 norm_a_sum = _mm256_setzero_ps();
    __m256 norm_b_sum = _mm256_setzero_ps();

    for (size_t i = 0; i < simd_size; i += 8) {
        __m256 va = _mm256_loadu_ps(&a[i]);
        __m256 vb = _mm256_loadu_ps(&b[i]);

        dot_sum = _mm256_add_ps(dot_sum, _mm256_mul_ps(va, vb));
        norm_a_sum = _mm256_add_ps(norm_a_sum, _mm256_mul_ps(va, va));
        norm_b_sum = _mm256_add_ps(norm_b_sum, _mm256_mul_ps(vb, vb));
    }

    // Horizontal sum
    float temp_dot[8], temp_a[8], temp_b[8];
    _mm256_storeu_ps(temp_dot, dot_sum);
    _mm256_storeu_ps(temp_a, norm_a_sum);
    _mm256_storeu_ps(temp_b, norm_b_sum);

    for (int i = 0; i < 8; ++i) {
        dot_product += temp_dot[i];
        norm_a += temp_a[i];
        norm_b += temp_b[i];
    }

    // Process remaining elements
    for (size_t i = simd_size; i < dimensions; ++i) {
        dot_product += a[i] * b[i];
        norm_a += a[i] * a[i];
        norm_b += b[i] * b[i];
    }

#else
    // Fallback: Scalar implementation
    for (size_t i = 0; i < dimensions; ++i) {
        dot_product += a[i] * b[i];
        norm_a += a[i] * a[i];
        norm_b += b[i] * b[i];
    }
#endif

    return dot_product / (std::sqrt(norm_a) * std::sqrt(norm_b));
}

/**
 * VectorBatchInserter
 * ===================
 *
 * High-performance batch vector insertion and search
 * - SIMD-optimized distance calculations
 * - Memory-efficient storage
 * - Linear search for baseline (HNSW in separate file)
 */
class VectorBatchInserter {
private:
    size_t dimensions_;
    size_t num_vectors_;
    std::vector<float> data_;  // Flat array of all vectors (row-major)

public:
    VectorBatchInserter(size_t dimensions)
        : dimensions_(dimensions), num_vectors_(0) {
        data_.reserve(1000000 * dimensions);  // Reserve space for 1M vectors
    }

    /**
     * Add single vector
     */
    void add(const std::vector<float>& vector) {
        if (vector.size() != dimensions_) {
            throw std::invalid_argument("Vector dimension mismatch");
        }

        data_.insert(data_.end(), vector.begin(), vector.end());
        num_vectors_++;
    }

    /**
     * Add batch of vectors (FAST!)
     *
     * Args:
     *   vectors: 2D vector of floats (each inner vector is one embedding)
     */
    void add_batch(const std::vector<std::vector<float>>& vectors) {
        for (const auto& vec : vectors) {
            if (vec.size() != dimensions_) {
                throw std::invalid_argument("Vector dimension mismatch");
            }
        }

        // Reserve space
        size_t total_elements = vectors.size() * dimensions_;
        data_.reserve(data_.size() + total_elements);

        // Batch insert (cache-friendly)
        for (const auto& vec : vectors) {
            data_.insert(data_.end(), vec.begin(), vec.end());
        }

        num_vectors_ += vectors.size();
    }

    /**
     * Search for k nearest neighbors (brute-force with SIMD)
     *
     * Args:
     *   query: Query vector
     *   k: Number of neighbors to return
     *
     * Returns:
     *   Vector of (index, distance) pairs sorted by distance
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

        // Calculate distances for all vectors (SIMD-optimized!)
        std::vector<std::pair<size_t, float>> distances;
        distances.reserve(num_vectors_);

        const float* query_ptr = query.data();

        for (size_t i = 0; i < num_vectors_; ++i) {
            const float* vector_ptr = &data_[i * dimensions_];
            float dist = l2_distance_simd(query_ptr, vector_ptr, dimensions_);
            distances.emplace_back(i, dist);
        }

        // Partial sort to get top k (O(n log k))
        std::partial_sort(
            distances.begin(),
            distances.begin() + k,
            distances.end(),
            [](const auto& a, const auto& b) { return a.second < b.second; }
        );

        // Return top k results
        distances.resize(k);
        return distances;
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
        num_vectors_ = 0;
    }
};

} // namespace native
} // namespace nexadb
