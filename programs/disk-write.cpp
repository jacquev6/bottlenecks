#include <numeric>
#include <fstream>
#include <filesystem>
#include <sstream>
#include <iomanip>
#include <vector>


int main(int argc, char* argv[]) {
  if (argc < 2) exit(1);
  const size_t size = std::atol(argv[1]);

  std::vector<char> data(size);
  std::iota(data.begin(), data.end(), 0);

  #pragma omp parallel for
  for (int i = 0; i < 1000; ++i) {
    std::ostringstream file_name;
    file_name << "build/io-" << std::setw(4) << std::setfill('0') << i << ".dat";
    {
      std::ofstream f(file_name.str());
      f.write(data.data(), data.size());
    }
    std::filesystem::remove(file_name.str());
  }
}
