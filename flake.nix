{
  description = "Nave — Python 3.9 development and build environment";

  inputs = {
    # Nave's pins are frozen around 2021 and five of them are C extensions
    # with no wheels on PyPI at cp39 (lxml, pyproj, shapely, psycopg2,
    # protobuf), so they compile from source against whatever system
    # libraries are present. That makes the library versions part of the
    # contract, not an implementation detail.
    #
    # This release reproduces the Debian 11 host almost exactly --
    # proj 7.2.1 to the patch version, geos 3.9.1, libxml2 2.9.12 -- and
    # still carries python39. A current nixpkgs does not: proj 9.x alone
    # breaks pyproj 2.6.1, which supports 6.2 through 7.x.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-21.05";
  };

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAll = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAll (pkgs: {
        default = pkgs.mkShell {
          packages = [
            pkgs.python39
            pkgs.python39Packages.pip
            pkgs.python39Packages.virtualenv

            # Toolchain the source builds need.
            pkgs.gcc
            pkgs.pkg-config

            # lxml 4.4.2 -- predates the libxml2 2.12 API changes.
            pkgs.libxml2
            pkgs.libxslt

            # pyproj 2.6.1 -- requires PROJ 6.2 to 7.x.
            pkgs.proj

            # shapely 1.5.17 -- finds libgeos_c through ctypes at import.
            pkgs.geos

            # psycopg2 2.8.4 -- needs pg_config and libpq.
            pkgs.postgresql

            # Pillow/colorific and filemagic.
            pkgs.zlib
            pkgs.libjpeg
            pkgs.freetype
            pkgs.file

            pkgs.openssl
            pkgs.git
          ];

          shellHook = ''
            # Each of these extensions locates its dependency differently:
            # pyproj reads PROJ_DIR, shapely shells out to geos-config, and
            # lxml uses pkg-config unless told to vendor its own copy.
            export PROJ_DIR=${pkgs.proj}
            export PROJ_LIB=${pkgs.proj}/share/proj
            export GEOS_CONFIG=${pkgs.geos}/bin/geos-config
            export LXML_STATIC_DEPS=false

            # nixpkgs splits headers into a separate `dev` output, so pyproj's
            # setup.py finds the library but not proj.h and stops with
            # "PROJ_INCDIR dir not found". Point it at both halves.
            export PROJ_INCDIR=${pkgs.proj.dev}/include
            export PROJ_LIBDIR=${pkgs.proj}/lib

            # shapely 1.5 and filemagic both dlopen their library by soname
            # at import time, so it has to be findable at runtime, not just
            # at build time.
            export LD_LIBRARY_PATH=${
              pkgs.lib.makeLibraryPath [
                pkgs.geos
                pkgs.proj
                pkgs.file
                pkgs.zlib
                pkgs.libxml2
                pkgs.libxslt
              ]
            }''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}

            echo "nave dev shell — python $(python3 --version 2>&1 | cut -d' ' -f2)"
            echo "  proj    ${pkgs.proj.version}"
            echo "  geos    ${pkgs.geos.version}"
            echo "  libxml2 ${pkgs.libxml2.version}"
          '';
        };
      });
    };
}
