# AAA Service Manager

This depends upon: 

* the [AAA SO](https://github.com/MobileCloudNetworking/aaaaas/tree/master/bundle)
* the MCN [SM framework](https://git.mobile-cloud-networking.eu/cloudcontroller/mcn_sm/tree/initial_sm_impl)
  * see documentation here

## Development

Get the source:

    $ git clone git@github.com/MobileCloudNetworking/aaaaas.git --recursive

### Dependencies
You will need to:

    $ pip install requests pyssf 

and:

    $ git clone git@git.mobile-cloud-networking.eu:cloudcontroller/mcn_sm.git
    $ cd mcn_sm
    $ python ./setup install

## Configuration
See: `./etc/sm.cfg`

Make sure to provide a valid RSA SSH key. DSS keys are not supported.

## Running
Execute this:

    $ python aaa_sm.py -c ./etc/sm.cfg
