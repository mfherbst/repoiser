# repoiser
Automatically checkout, build and test a set of depending repositories

Currently this only works very well for the repositories used for `adcman` and `ccman2` within the Q-Chem quantum chemistry project,
although parts of the project are very general (like the dependency resolution between the different repositories) and could
be generalised easily very soon.

Documentation is also on the TODO ...

# How to use the examples
## Standalone adcman
To compile standalone `adcman` run for example
```
./setup_checkout.sh examples/adcman.yaml && ./configure_build_test.sh
```

## adcman and ccman2 from svn
To compile the most recent `ccman2` and `adcman` straight from the relevent developer branches run
```
./setup_checkout.sh examples/qchem_adcccman_all.yaml && \
	./configure_build_test.sh
```
