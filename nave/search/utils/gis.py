import math

from pyproj import transform, Proj


# Proj4 projection strings.  Note: no commas between the concatenated strings!
RD = ("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 "
      "+k=0.999908 +x_0=155000 +y_0=463000 +ellps=bessel "
      "+towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 "
      "+units=m +no_defs")
GOOGLE = ('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 '
          '+lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m '
          '+nadgrids=@null +no_defs +over')
WGS84 = ('+proj=latlong +datum=WGS84')

# Rijksdriehoeks stelsel.
rd_projection = Proj(RD)
google_projection = Proj(GOOGLE)
wgs84_projection = Proj(WGS84)


def standard_percision(x):
    """Return a standard percision of 6. """
    return math.ceil(x*1000000)/1000000


def rd_to_wgs84(x, y, standard=True):
    """Return GOOGLE coordinates from RD coordinates.

    >>> rd_to_wgs84(85530,446100)
    (4.375585, 51.998928)

    """
    east, north = transform(rd_projection, wgs84_projection, x, y)
    lat_long = (standard_percision(east), standard_percision(north)) if standard else (east, north)
    return lat_long
