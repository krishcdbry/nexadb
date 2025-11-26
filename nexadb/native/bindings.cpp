/*
 * NexaDB Python Bindings
 * ======================
 *
 * pybind11 bindings for C++ vector operations
 * Exposes high-performance C++ code to Python
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>  // Automatic conversion for std::vector
#include <pybind11/numpy.h>  // Numpy array support

#include "vector_ops.cpp"
#include "hnsw_index.cpp"

namespace py = pybind11;
using namespace nexadb::native;

PYBIND11_MODULE(nexadb_native, m) {
    m.doc() = "NexaDB native C++ vector operations (50-100x faster than Python!)";

    // VectorBatchInserter class
    py::class_<VectorBatchInserter>(m, "VectorBatchInserter")
        .def(py::init<size_t>(),
             py::arg("dimensions"),
             "Create a new batch inserter\n\n"
             "Args:\n"
             "    dimensions: Vector dimensionality (e.g., 768 for OpenAI embeddings)")

        .def("add",
             &VectorBatchInserter::add,
             py::arg("vector"),
             "Add single vector\n\n"
             "Args:\n"
             "    vector: List of floats")

        .def("add_batch",
             &VectorBatchInserter::add_batch,
             py::arg("vectors"),
             "Add batch of vectors (FAST!)\n\n"
             "Args:\n"
             "    vectors: List of lists of floats (2D array)\n\n"
             "Example:\n"
             "    >>> inserter = VectorBatchInserter(768)\n"
             "    >>> vectors = [[0.1, 0.2, ...], [0.3, 0.4, ...]]\n"
             "    >>> inserter.add_batch(vectors)")

        .def("search",
             &VectorBatchInserter::search,
             py::arg("query"),
             py::arg("k") = 10,
             "Search for k nearest neighbors\n\n"
             "Args:\n"
             "    query: Query vector (list of floats)\n"
             "    k: Number of neighbors to return (default: 10)\n\n"
             "Returns:\n"
             "    List of (index, distance) tuples sorted by distance\n\n"
             "Example:\n"
             "    >>> query = [0.5, 0.6, ...]\n"
             "    >>> results = inserter.search(query, k=10)\n"
             "    >>> for idx, dist in results:\n"
             "    ...     print(f'Vector {idx}: distance={dist}')")

        .def("size",
             &VectorBatchInserter::size,
             "Get number of vectors")

        .def("dimensions",
             &VectorBatchInserter::dimensions,
             "Get vector dimensions")

        .def("clear",
             &VectorBatchInserter::clear,
             "Clear all vectors")

        .def("__len__",
             &VectorBatchInserter::size,
             "Get number of vectors (len(inserter))")

        .def("__repr__",
             [](const VectorBatchInserter& self) {
                 return "<VectorBatchInserter(dimensions=" +
                        std::to_string(self.dimensions()) +
                        ", vectors=" +
                        std::to_string(self.size()) +
                        ")>";
             });

    // HNSWIndex class
    py::class_<HNSWIndex>(m, "HNSWIndex")
        .def(py::init<size_t, size_t, size_t, size_t>(),
             py::arg("dimensions"),
             py::arg("max_elements") = 1000000,
             py::arg("M") = 16,
             py::arg("ef_construction") = 200,
             "Create a new HNSW index\n\n"
             "Args:\n"
             "    dimensions: Vector dimensionality\n"
             "    max_elements: Maximum number of elements (default: 1M)\n"
             "    M: Number of connections per layer (default: 16)\n"
             "    ef_construction: Construction-time search depth (default: 200)")

        .def("add",
             &HNSWIndex::add,
             py::arg("vector"),
             "Add single vector to HNSW index\n\n"
             "Args:\n"
             "    vector: List of floats")

        .def("add_batch",
             &HNSWIndex::add_batch,
             py::arg("vectors"),
             "Add batch of vectors to HNSW index\n\n"
             "Args:\n"
             "    vectors: List of lists of floats")

        .def("search",
             &HNSWIndex::search,
             py::arg("query"),
             py::arg("k") = 10,
             "Search for k nearest neighbors (approximate)\n\n"
             "Args:\n"
             "    query: Query vector (list of floats)\n"
             "    k: Number of neighbors to return (default: 10)\n\n"
             "Returns:\n"
             "    List of (index, distance) tuples sorted by distance")

        .def("set_ef",
             &HNSWIndex::set_ef,
             py::arg("ef"),
             "Set search-time ef parameter (higher = more accurate, slower)\n\n"
             "Args:\n"
             "    ef: Search depth (default: 100)")

        .def("size",
             &HNSWIndex::size,
             "Get number of vectors in index")

        .def("dimensions",
             &HNSWIndex::dimensions,
             "Get vector dimensions")

        .def("clear",
             &HNSWIndex::clear,
             "Clear all vectors from index")

        .def("__len__",
             &HNSWIndex::size,
             "Get number of vectors (len(index))")

        .def("__repr__",
             [](const HNSWIndex& self) {
                 return "<HNSWIndex(dimensions=" +
                        std::to_string(self.dimensions()) +
                        ", vectors=" +
                        std::to_string(self.size()) +
                        ", type=HNSW)>";
             });

    // Version info
    m.attr("__version__") = "2.2.0";
    m.attr("__simd__") =
#if defined(__ARM_NEON) || defined(__aarch64__)
        "ARM_NEON";
#elif defined(__AVX2__)
        "AVX2";
#else
        "SCALAR";
#endif
}
