## [1.1.0](https://github.com/sean2077/jsonpath-python/compare/v1.0.5...1.1.0) (2025-11-23)

### Fixes

* modernize project structure and fix path output ([#7](https://github.com/sean2077/jsonpath-python/issues/7)) ([7713759](https://github.com/sean2077/jsonpath-python/commit/7713759874626fb9595c58d7e7f8e6a6cee2c7ce))
* resolve issue [#10](https://github.com/sean2077/jsonpath-python/issues/10) by raising JSONPathTypeError on mixed type sorting ([8ac2080](https://github.com/sean2077/jsonpath-python/commit/8ac2080c1ff5b520b66a8e5f22a6d0a025d6776f))
* resolve issue [#15](https://github.com/sean2077/jsonpath-python/issues/15) where filters with bracket notation returned empty results ([100bf6f](https://github.com/sean2077/jsonpath-python/commit/100bf6fda10d9802cff7223e443a11fb63f1409a))
* resolve issue [#16](https://github.com/sean2077/jsonpath-python/issues/16) support quoted keys in filters and paths ([6caa9d4](https://github.com/sean2077/jsonpath-python/commit/6caa9d4e0e9a95363edc6024b41d5b8ea5e785c0))
* resolve issue [#17](https://github.com/sean2077/jsonpath-python/issues/17) false positive errors and parsing bugs ([47bba25](https://github.com/sean2077/jsonpath-python/commit/47bba251233b8f96963dc22e2e83238b417e332a))
* resolve issue [#9](https://github.com/sean2077/jsonpath-python/issues/9) by filtering out missing keys in field extractor ([5e38031](https://github.com/sean2077/jsonpath-python/commit/5e38031611c3623910150320760abd5c852c93aa))

### Features

* add search and complie interfaces ([8dcf854](https://github.com/sean2077/jsonpath-python/commit/8dcf854d467ebf1dfa3587eedfb5292ebc089c78))
* add update function to JSONPath class ([#12](https://github.com/sean2077/jsonpath-python/issues/12)) ([d396bc5](https://github.com/sean2077/jsonpath-python/commit/d396bc5c2e19d3f081a76eed7e95a893f0d7cd5e))
* Custom eval implementation ([22d7154](https://github.com/sean2077/jsonpath-python/commit/22d7154560dbc3eca2e6025f95cce4dd4b8654d9))
* resolve issue [#13](https://github.com/sean2077/jsonpath-python/issues/13) by adding support for 'in' operator and regex matching (=~) ([a5e2973](https://github.com/sean2077/jsonpath-python/commit/a5e2973b42f1d6b14d20cae48f250501cb81d341))

# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [1.0.5](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/compare/v1.0.4...v1.0.5) (2021-03-02)


### Features

* bump version 1.0.5 ([d5036a4](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/d5036a4cba6d32ecf8b679d48493125e067cb9a4))


### Bug Fixes

* fix sorter by number string ([8712e4c](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/8712e4c995d0ced09b79b32211155e2567f69564))

### [1.0.4](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/compare/v1.0.3...v1.0.4) (2021-03-02)


### Features

* bump version 1.0.4 ([5ea02a6](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/5ea02a67bec39ca50ffe141578fdbc5821fa8213))


### Bug Fixes

* fix setup.py ([5ba778b](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/5ba778bf877211b9834dd71fc2cb1ae3daa52876))

### [1.0.3](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/compare/v1.0.2...v1.0.3) (2021-03-02)


### Features

* bump version v1.0.3 ([122fa54](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/122fa54fa0051bafeb8f1e64cd1a9fc1b91b3610))
* support child operator in field-selector ([f5ec645](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/f5ec645673df67baee248431860ada082fe95006))

### [1.0.2](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/compare/v1.0.1...v1.0.2) (2021-01-13)


### Features

* bump version v1.0.2 ([36f7bfa](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/36f7bfa51c2bb6ac0991a3f85fac8a4c4e67972e))
* complete jsonpath syntax ([cca9583](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/cca9583f7910f3abf183f6056103f9dc24d75f0d)), closes [#1](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/issues/1)
* improve regex pattern of select content ([264c2ea](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/264c2ea35cdbdc5806093b27a2b409ca609ecde1))

### 1.0.1 (2021-01-04)


### Features

* add jsonpath ([c3fc7b0](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/c3fc7b0c4620327d33a2f0bcfe7b2befcbdbd9ff))
* add output mode: PATH ([3e2bcda](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/3e2bcda7fbbd7636786bd28549253a40bb0d5a28))
* bump version 0.0.3 ([14da85e](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/14da85e1bda03dd403fd32c71e53dbafac16ec5d))
* bump version 1.0.0 ([292daff](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/292daff3bfcbde3715d460dcdb9fe6f53921a4b8))
* bump version 1.0.1 ([f7ad9e1](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/f7ad9e13d1e37f66285bb26bbf2696553a735b03))
* support operator: field-extractor ([4645c33](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/4645c33a54dda9705c3422c4f18bbfc7d0c9c986))
* support sorting dict ([4922c94](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/4922c949bf5d74d878b131e2ed70b7d476b3cce0))


### Bug Fixes

* fix path mode & add unit tests ([18059d7](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/18059d70e5f808b94b6d381531907b9a8039a111))
* fix unnecessary-comprehension ([77ad2db](https://gitlab.sz.sensetime.com/its-engineering/toolkit/jsonpath-python/commit/77ad2dbcabd11ac66708b5b9aea226700170fe7f))
