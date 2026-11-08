# Parallel computing: CUDA matrix multiplication and a concurrent hash table

Two parallel-programming projects from my coursework at Sharif University of Technology: GPU kernels for dense matrix multiplication, and a multithreaded hash table in C with Pthreads.

## 1. CUDA matrix multiplication (`cuda-matmul/`)

Three versions of `C = A × B` for 10240 × 10240 single-precision matrices, each checked against a reference result (0 wrong elements in every run).

| Kernel | Idea | Time |
|---|---|---|
| `gpu_naive.cu` | one thread per output element, all reads from global memory | 35.18 s |
| `gpu_tiled.cu` | 32 × 32 tiles of A and B loaded into shared memory, reused by the whole block | 4.36 s |
| `gpu_tiled_offsets.cu` | the same tiling with row/column offsets precomputed outside the loop | 2.50 s |

Tiling gives an **8× speedup** over the naive kernel by cutting global-memory traffic. The third version adds about another 1.7×, so about **14× in total**. These are single runs on a Google Colab GPU, so treat the last step as indicative rather than a precise measurement. `cpu_matmul.c` is a sequential CPU reference on a smaller 1024 × 1024 matrix (not timed on the same size).

```bash
nvcc -O3 -o gpu_tiled cuda-matmul/gpu_tiled.cu && ./gpu_tiled
```
The kernels assume the matrix size is a multiple of the 32 × 32 tile.

## 2. Concurrent hash table (`concurrent-hash-table/`)

A chained hash table (djb2 hash) that processes large key files with many threads.
- **Fine-grained locking:** one mutex per bucket, so threads working on different buckets never block each other.
- **Lazy deletion:** deleted keys are marked with a tombstone and revived if inserted again.
- **Static partitioning:** each input file is split into equal chunks, one per thread; the collision counter is updated atomically.
- For each key the program reports its bucket and whether it already existed (insert) or was found (delete), plus execution time and the number of collisions handled.

```bash
make all
./bin/concurrent_hash_table --data_size 150K --threads 8 --tsize 300K \
    --flow insert delete --input keys1.txt keys2.txt
make test-all && make analyze   # benchmark grid (threads × table size) and plots
```
The benchmark scripts expect input files under `inputs/` (not included: about 40 MB of generated keys).

**Fixes made when publishing:** a stray character that broke compilation, a crash when an input file has fewer lines than `--data_size`, and course-specific file names.

## License
MIT, see [LICENSE](LICENSE).
