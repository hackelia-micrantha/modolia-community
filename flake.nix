{
  description = "Modolia community deterministic model-surface resolver";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          modolia = pkgs.callPackage ./nix/package.nix { };
        in
        {
          default = modolia;
          modolia = modolia;
          # Temporary compatibility alias for existing consumers.
          model-router = modolia;
        }
      );

      apps = forAllSystems (system: {
        default = self.apps.${system}.modolia;
        modolia = {
          type = "app";
          program = "${self.packages.${system}.modolia}/bin/modolia";
        };
      });

      formatter = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        pkgs.nixfmt-rfc-style
      );

      checks = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          validationPython = pkgs.python312.withPackages (pythonPackages: [
            pythonPackages.jsonschema
            pythonPackages.pytest
            pythonPackages.pytest-cov
            pythonPackages.pyyaml
          ]);
        in
        {
          package = self.packages.${system}.default;

          executable = pkgs.runCommand "modolia-community-executable" { } ''
            ${self.packages.${system}.modolia}/bin/modolia --help > /dev/null
            test "$(${self.packages.${system}.modolia}/bin/modolia --version)" = \
              "modolia 0.1.0 (resolver 0.1.0)"
            ${self.packages.${system}.modolia}/bin/modolia \
              ${./examples/route-request.json} \
              ${./examples/route-constraints.json} \
              --registry ${./examples/model-surfaces.yaml} \
              > decision.json
            test -s decision.json
            mkdir -p $out
            cp decision.json $out/decision.json
          '';

          static-analysis = pkgs.runCommand "modolia-community-static-analysis" {
            nativeBuildInputs = [
              pkgs.mypy
              pkgs.ruff
            ];
          } ''
            cp -r ${./.} source
            chmod -R u+w source
            cd source

            ruff check model_router scripts tests
            mypy model_router scripts/resolve_route.py

            mkdir -p $out
            echo ok > $out/result
          '';

          unit = pkgs.runCommand "modolia-community-unit-tests" {
            nativeBuildInputs = [ validationPython ];
          } ''
            cp -r ${./.} source
            chmod -R u+w source
            cd source

            pytest -q tests/unit

            mkdir -p $out
            echo ok > $out/result
          '';

          integration = pkgs.runCommand "modolia-community-integration-tests" {
            nativeBuildInputs = [ validationPython ];
          } ''
            cp -r ${./.} source
            chmod -R u+w source
            cd source

            pytest -q -m integration tests/integration

            mkdir -p $out
            echo ok > $out/result
          '';

          coverage = pkgs.runCommand "modolia-community-coverage" {
            nativeBuildInputs = [ validationPython ];
          } ''
            cp -r ${./.} source
            chmod -R u+w source
            cd source

            pytest -q --cov --cov-report=term-missing tests/unit tests/integration

            mkdir -p $out
            echo ok > $out/result
          '';

          e2e = pkgs.runCommand "modolia-community-e2e-tests" {
            nativeBuildInputs = [ validationPython ];
          } ''
            cp -r ${./.} source
            chmod -R u+w source
            cd source

            pytest -q -m e2e tests/e2e

            mkdir -p $out
            echo ok > $out/result
          '';
        }
      );

      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.mypy
              pkgs.ruff
              (pkgs.python312.withPackages (pythonPackages: [
                pythonPackages.jsonschema
                pythonPackages.pytest
                pythonPackages.pytest-cov
                pythonPackages.pyyaml
              ]))
            ];
          };
        }
      );
    };
}
