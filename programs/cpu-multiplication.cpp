// Copyright 2022 Vincent Jacques

#include <cstdlib>


int main(int argc, char* argv[]) {
  if (argc < 2) exit(1);
  const int size = 1024 * std::atoi(argv[1]);

  #pragma omp parallel for
  for (int i = 0; i < 1024; ++i) {
    volatile double x = 3.14;
    for (int j = 0; j != size; ++j) {
      x *= i;
    }
  }
}
