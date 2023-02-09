# ewx_pws

Python package for collecting, transforming and aggregating weat data from commercial weather stations, based on the package 

To support for MSU Enviroweather Network Personal Weather Station project. 

This code is in very early stages of development and for use by the EWX team only. 

## Installation

```bash
$ pip install ewx_pws
```

## Usage

Given a CSV file with weather stations configuration in it, To pull recent data, in this root folder, use 

`python bin/getweather.py /path/to/stations.csv`

To see usage and other options for this CLI, use

`python bin/getweather.py -h`

## Contributing

We are not seeking contributions at this stage.   EWX staff, see [contributing](docs/contributing.md) for development documentation. 

## License

`ewx_pws` was created by the MSU Enviroweather Team, currently licensed under the terms of the MIT license.

## Credits

Initial `ewx_pws` package was created with [`cookiecutter`](https://cookiecutter.readthedocs.io/en/latest/) and the `py-pkgs-cookiecutter` [template](https://github.com/py-pkgs/py-pkgs-cookiecutter).

Based on the [MultiWeatherAPI package](https://github.com/billspat/multiweatherapi/) by Junhee Park 
