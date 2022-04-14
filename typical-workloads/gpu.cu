// Copyright 2022 Vincent Jacques

#include <cstdlib>


#define BLOCK_SIZE 512

__global__ void kernel(double* x, const int repetitions) {
  x[threadIdx.x] = 3.14;
  for (int j = 0; j != repetitions; ++j) {
    x[threadIdx.x] *= j;
  }
}

int main(int argc, char* argv[]) {
  if (argc < 2) exit(1);
  const int multiplier = std::atoi(argv[1]);
  if (multiplier < 1 || multiplier > 1024) exit(1);
  const int repetitions = 1024 * 1024 * multiplier;

  double* d_x;
  cudaMalloc(&d_x, BLOCK_SIZE * sizeof(double));
  kernel<<<1, BLOCK_SIZE>>>(d_x, repetitions);
  double x[BLOCK_SIZE];
  cudaMemcpy(x, d_x, BLOCK_SIZE * sizeof(double), cudaMemcpyDeviceToHost);
  cudaFree(d_x);
}
