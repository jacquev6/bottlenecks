// Copyright 2022 Vincent Jacques

#include <stdlib.h>
#include <math.h>


int main(int argc, char* argv[]) {
  if (argc < 2) exit(1);
  const int size = 1024 * atoi(argv[1]);

  bool ok = true;

  #pragma omp parallel for
  for (int i = 0; i < 1024; ++i) {
    for (int j = 0; j != size; ++j) {
      double x = i * size + j;
      if (acos(cos(x)) < 0) {
        ok = false;
        break;
      }
    }
  }

  return ok ? 0 : 1;
}
