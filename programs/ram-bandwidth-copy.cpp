// This is similar to the STREAM bandwidth benchmark
// https://www.cs.virginia.edu/stream/

#include <cstdlib>
#include <vector>


int main(int argc, char* argv[]) {
  if (argc < 2) exit(1);
  const std::size_t size = 1024 * 1024 * std::atol(argv[1]);

  std::vector<int> a(size, 42);
  std::vector<int> b(size, 0);

  for (int i = 0; i != 100; ++i) {
    #pragma omp parallel for
    for (std::size_t j = 0; j < size; ++j) {
      b[j] = a[j];
    }
  }

  return b[0] == 42 && b[size - 1] == 42 ? 0 : 1;
}
