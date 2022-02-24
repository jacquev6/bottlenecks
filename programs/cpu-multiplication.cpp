#include <stdlib.h>
#include <math.h>


int main(int argc, char* argv[]) {
  if (argc < 2) exit(1);
  const int size = 1024 * atoi(argv[1]);

  bool ok = true;

  #pragma omp parallel for
  for (int i = 0; i < 1024; ++i) {
    double x = 3.14;
    for (int j = 0; j != size; ++j) {
      x *= i;
      if (x < 0) {
        ok = false;
        break;
      }
    }
  }

  return ok ? 0 : 1;
}
