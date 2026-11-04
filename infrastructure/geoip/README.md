# GeoIP (GeoLite2)

The API mounts this directory at `/geoip` inside the container. If a valid
`GeoLite2-City.mmdb` is present here, `GET /api/v1/geo/detect` will use it to
resolve the caller's IP to a city; otherwise the endpoint returns
`{ "location": null, "source": "unknown" }` and the browser Geolocation API
becomes the primary signal.

## Getting the MaxMind GeoLite2 database (free, requires signup)

1. Create a free account at https://www.maxmind.com/en/geolite2/signup
2. Generate a license key.
3. Download the `GeoLite2-City` MMDB (binary format).
4. Extract and drop `GeoLite2-City.mmdb` into this directory.

The file is git-ignored — do not commit it.

## Automated refresh (optional)

MaxMind publishes a small updater tool called `geoipupdate`. Keeping the DB
fresh (weekly) improves accuracy. Point it at the same path.
