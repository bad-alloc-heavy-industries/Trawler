# Trawler - Bulk download of datasheets

Trawler is an application to help in the facilitation of bulk downloads for datasheets and resources from vendor websites.

This comes about because vendors don't tend to host bulk downloads of their content, or something nice like an rsync mirror, rather we need to result to scraping.

Trawler is built around selenium, which allows us to pretend to be a user and let AJAX and other bits of JavaSctript run to allow us to interact with the vendor website and collect the datasheets.


## Adapters

The following adapters are included with Trawler:
 * `arm` - Download documentation from `https://developer.arm.com/documentation`
 * `xilinx` - Download the documentation from the Xilinx DocNav service

The following adapters are planned:
 * `usb-if` - Download the documentation from `https://www.usb.org/documents`
 * `renasas` - Download the documentation from `https://www.renesas.com/us/en/support/document-search`

If there is not an adapter in this list you want, feel free to open an issue or contribute it yourself!

## Usage

To use Trawler, in the most simple way, simply invoke the adapter for the datasheet source you want, like so:
```
trawler arm
```

This will cause Trawler to initialize everything it needs and then it will automatically start the entire acquisition process. This will absolutely take a long time, and the length of which heavily depends on the adapter.

Each adapter has their own settings and configuration in addition to the global settings, to see the settings the adapter support, simply issue `--help` to it:
```
trawler arm --help
```

To list the adapters that Trawler knows about, simply pass `--help` to Trawler by itself and it will let you know about all the adapters it has
```
trawler --help
```

### Global Settings

Trawler supports the following settings globally:
 * `--output / -o` - Specify the output directory for Trawler to use.
 * `--timeout / -t` - Specify the timeout duration in seconds for network operations.
 * `--retry / -r` - Specify the number of times to retry network operations.
 * `--delay / -d` - Specify the delay in seconds for network operations.
 * `--cache-database / -c` - Specify the location and name of the datasheet cache database Trawler uses.
 * `--skip-collect / -C` - Skip the datasheet collection stage for the adapter.
 * `--skip-extract / -E` - Skip the extraction stage for the adapter.
 * `--skip-download / -D` - Skip the download stage for the adapter.

The following settings are used for the WebDriver, and therefore only effect the adapters / stages that use it:
 * `--profile-directory / -p` - Specify the WebDriver profile directory.
 * `--webdriver / -w` - Specify the WebDriver to use.
 * `--headless / -H` - Tell the WebDriver to run in headless mode.
 * `--headless-width / -X` - Specify the virtual width of the WebDriver instance.
 * `--headless-height / -Y` - Specify the virtual hight of the WebDriver instance.

### ARM Adapter Settings

The following settings are only applicable to the ARM adapter:
 * `--arm-document-type / -A` - Specify the types of documents to collect and download.


### Xilinx Adapter Settings

The following settings are only applicable to the Xilinx adapter:
 * `--dont-group / -G` - Don't group Datasheets into categories and groups when downloading.
 * `--collect-web-only / -W` - Allow Trawler to collect the web-only content.
 
## Installing

With pip, all the needed dependencies for Trawler should be pulled in automatically

To install the current development snapshot, simply run:
```
pip3 install --user 'git+https://github.com/bad-alloc-heavy-industries/Trawler.git#egg=Trawler'
```
Or to install a local development copy:
```
git clone https://github.com/bad-alloc-heavy-industries/Trawler.git
cd Trawler
pip3 install --user --editable '.''
```

## Important Notes

 * Some adapters won't work if the WebDriver viewport is smaller than 1920x1080, you can possibly fix this by running the WebDriver headless with the correct virtual size if the WebDriver supports it.

## License
Trawler is licensed under the [BSD 3-Clause](https://spdx.org/licenses/BSD-3-Clause.html) license, the full text of which can be found in the [`LICENSE`](LICENSE) file.
