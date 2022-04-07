// Copyright 2022 Vincent Jacques

#include <cstdlib>


int main(int argc, char* argv[]) {
  if (argc < 2) exit(1);
  const int multiplier = std::atoi(argv[1]);
  if (multiplier < 1 || multiplier > 1024) exit(1);
  const int repetitions = 1024 * 1024 * multiplier;

  #pragma omp parallel for
  for (int i = 0; i < 1024; ++i) {
    volatile double x = 3.14;
    for (int j = 0; j != repetitions; ++j) {
      x *= j;
    }
  }
}
