class YourPackage < Formula
    include Language::Python::Virtualenv
    
    desc "Brief description of your package"
    homepage "https://github.com/raghavpillai/autocommit"
    url "https://files.pythonhosted.org/packages/source/y/your_package/your_package-0.1.0.tar.gz"
    sha256 "the_sha256_hash_of_your_package_tarball"
    license "MIT"
  
    depends_on "python@3.12"
  
    def install
      virtualenv_install_with_resources
    end
  
    test do
      # Add a test command here
      system "#{bin}/autocommit", "--version"
    end
  end