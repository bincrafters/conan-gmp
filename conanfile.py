import os
import stat
from conans import ConanFile, tools, AutoToolsBuildEnvironment
from conans.errors import ConanInvalidConfiguration


class GmpConan(ConanFile):
    name = "gmp"
    version = "6.1.2"
    url = "https://github.com/bincrafters/conan-gmp"
    homepage = "https://gmplib.org"
    description = "GMP is a free library for arbitrary precision arithmetic, operating on signed integers, rational numbers, and floating-point numbers."
    author = "Bincrafters <bincrafters@gmail.com>"
    license = ("LGPL-3.0", "GPL-2.0")
    exports = ["LICENSE.md"]
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "disable_assembly": [True, False],
               "run_checks": [True, False],"enable_cxx" : [True, False]}
    default_options = {'shared': False, 'fPIC': True, 'disable_assembly': True, 'run_checks': False, "enable_cxx" : True}
    _autotools = None
    
    def build_requirements(self):
        if not tools.which("m4"):
            self.build_requires("m4_installer/1.4.18@bincrafters/stable")

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def configure(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("The gmp package cannot be deployed on Visual Studio.")

        if not self.options.enable_cxx:
            del self.settings.compiler.libcxx
            del self.settings.compiler.cppstd

    def source(self):
        sha256 = "5275bb04f4863a13516b2f39392ac5e272f5e1bb8057b18aec1c9b79d73d8fb2"
        source_url = "{}/download/gmp".format(self.homepage)
        tools.get("{0}/{1}-{2}.tar.bz2".format(source_url, self.name, self.version), sha256=sha256)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_autotools(self):
        if not self._autotools:
            self._autotools = AutoToolsBuildEnvironment(self)
            if self.settings.os == "Macos":
                configure_file = os.path.join(self._source_subfolder, "configure")
                tools.replace_in_file(configure_file, r"-install_name \$rpath/", "-install_name ")
                configure_stats = os.stat(configure_file)
                os.chmod(configure_file, configure_stats.st_mode | stat.S_IEXEC)
            configure_args = []
            if self.options.disable_assembly:
                configure_args.append('--disable-assembly')
            if self.options.shared:
                configure_args.extend(["--enable-shared", "--disable-static"])
            else:
                configure_args.extend(["--disable-shared", "--enable-static"])
            if self.options.enable_cxx:
                configure_args.append('--enable-cxx')
            self._autotools.configure(args=configure_args, configure_dir=self._source_subfolder)
        return self._autotools

    def build(self):
        autotools = self._configure_autotools()
        autotools.make()
        # INFO: According to the gmp readme file, make check should not be omitted, but it causes timeouts on the CI server.
        if self.options.run_checks:
            autotools.make(args=['check'])

    def package(self):
        self.copy("COPYINGv2", dst="licenses", src=self._source_subfolder)
        self.copy("COPYING.LESSERv3", dst="licenses", src=self._source_subfolder)
        autotools = self._configure_autotools()
        autotools.install()
        tools.rmdir(os.path.join(self.package_folder, "share"))
        la = os.path.join(self.package_folder, "lib", "libgmp.la")
        if os.path.isfile(la):
            os.unlink(la)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
