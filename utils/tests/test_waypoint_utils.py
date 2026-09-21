"""
TODO(bootcamper): write the tests for ``src/waypoint_utils.py`` in here.

The example below covers files that parse fine: with and without ``home``,
and files with comments and blank lines in them. The rest is yours:

- Bad data: a file whose top level isn't a mapping, waypoints missing
  ``lat``, ``lon``, or ``alt``, values that aren't numbers, YAML that
  doesn't parse, and a file that isn't there.
- Out of range: latitudes past +/-90 and longitudes past +/-180 get
  rejected.
- Nothing to work with: an empty file, an empty ``waypoints`` list, and
  ``sort_clockwise_sweep`` given a list of 0 or 1 waypoints.
- ``east_north_coordinate_offset_m``: offsets you worked out yourself,
  compared with ``pytest.approx``. Never use ``==`` on meters.
- Ordering: with no ``home``, ``sort_clockwise_sweep`` goes clockwise
  starting from north.
- With a ``home``: the order starts in home's direction instead, and goes
  back to starting at north if home is right on top of the centroid.
- Two waypoints in the same direction: the closer one comes first.
- Parsing gives you frozen ``Coordinate`` objects that can't be changed.

Graded by ``warg run utils grade-tests``: pass on the real code, 90% branch
coverage, and fail on every broken copy in ``grader/mutants/``.
"""
import math

import pytest

from src.constants import EARTH_RADIUS_M
from src.types import Coordinate
from src.waypoint_utils import (
    east_north_coordinate_offset_m,
    parse_waypoints_file,
    sort_clockwise_sweep,
)

# The helper and the test below are given to you.


def write_to_tmp_waypoints_file(tmp_path, text):
    """Write ``text`` to a YAML file and hand back its path.

    ``tmp_path`` is a pytest fixture: a fresh empty directory per test.
    """
    path = tmp_path / "waypoints.yaml"
    path.write_text(text)
    return path


# One test, three files. ``parametrize`` runs the test body once per
# ``(text, expected)`` pair, and ``ids`` names each run so a failure tells you
# which file broke.
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            """
            home: {lat: 1, lon: 2, alt: 3}
            waypoints:
              - {lat: 4, lon: 5, alt: 6}
            """,
            (Coordinate(1, 2, 3), [Coordinate(4, 5, 6)]),
        ),
        (
            """
            waypoints:
              - {lat: 4, lon: 5, alt: 6}
              - {lat: 7, lon: 8, alt: 9}
            """,
            (None, [Coordinate(4, 5, 6), Coordinate(7, 8, 9)]),
        ),
        (
            """
            # a lap

            home: {lat: 1, lon: 2, alt: 3}

            waypoints:
              # first leg
              - {lat: 4, lon: 5, alt: 6}
            """,
            (Coordinate(1, 2, 3), [Coordinate(4, 5, 6)]),
        ),
    ],
    ids=["home-and-waypoints", "no-home", "comments-and-blank-lines"],
)
def test_parse_waypoints_file_success(tmp_path, text, expected):
    path = write_to_tmp_waypoints_file(tmp_path, text)
    assert parse_waypoints_file(path) == expected

def test_parse_empty_file(tmp_path):
    path = write_to_tmp_waypoints_file(tmp_path, "")
    result = parse_waypoints_file(path)
    assert result == (None, [])
def test_parse_waypoint_missing_alt(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        "waypoints:\n  - {lat: 4, lon: 5}\n",
    )
    with pytest.raises(ValueError):
        parse_waypoints_file(path)
def test_parse_latitude_out_of_range(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        "waypoints:\n  - {lat: 91, lon: 5, alt: 10}\n",
    )
    with pytest.raises(ValueError):
        parse_waypoints_file(path)
def test_parse_nonnumeric_latitude(tmp_path):
    path = write_to_tmp_waypoints_file(
        tmp_path,
        "waypoints:\n  - {lat: hello, lon: 5, alt: 10}\n",
    )
    with pytest.raises(ValueError):
        parse_waypoints_file(path)
def test_same_location_has_zero_offset():
    east, north = east_north_coordinate_offset_m(
        43.0, -80.0, 43.0, -80.0
    )
    assert east == pytest.approx(0.0, abs=1e-6)
    assert north == pytest.approx(0.0, abs=1e-6)
def test_one_degree_north():
    east, north = east_north_coordinate_offset_m(
        0.0, 0.0, 1.0, 0.0
    )
    assert east == pytest.approx(0.0, abs=1e-6)
    assert north == pytest.approx(
        EARTH_RADIUS_M * math.pi / 180,
        abs=1e-6,
    )
def test_sort_clockwise_from_north():
    north = Coordinate(1, 0, 10)
    east = Coordinate(0, 1, 10)
    south = Coordinate(-1, 0, 10)
    west = Coordinate(0, -1, 10)

    result = sort_clockwise_sweep([south, west, north, east])

    assert result == [north, east, south, west]
def test_sort_clockwise_from_home():
    north = Coordinate(1, 0, 10)
    east = Coordinate(0, 1, 10)
    south = Coordinate(-1, 0, 10)
    west = Coordinate(0, -1, 10)

    result = sort_clockwise_sweep(
        [south, west, north, east],
        home=east,
    )

    assert result == [east, south, west, north]
def test_sort_empty_waypoints():
    assert sort_clockwise_sweep([]) == []


def test_sort_single_waypoint():
    waypoint = Coordinate(1, 2, 10)

    assert sort_clockwise_sweep([waypoint]) == [waypoint]
def test_parse_rejects_top_level_list(tmp_path):
    path = write_to_tmp_waypoints_file(tmp_path, "[]")

    with pytest.raises(ValueError):
        parse_waypoints_file(path)
def test_same_bearing_nearest_first():
     near = Coordinate(1,0, 10)
     far = Coordinate(2,0,10)
     south = Coordinate(-3, 0, 10)

     result = sort_clockwise_sweep([far, south, near])

     assert result == [near,far,south]
def test_east_offset_at_high_latitude():
    east, north = east_north_coordinate_offset_m(
        60.0, 0.0, 60.0, 1.0
    )
    expected_east = EARTH_RADIUS_M * math.pi / 180 * 0.5

    assert east == pytest.approx(expected_east, abs= 1e-6)

    assert north == pytest.approx(0.0, abs = 1e-6)
def test_placeholder():
    # TODO(bootcamper): delete this and write real tests. It's only here so
    # linter doesn't complain about unused imports before you start.
    assert callable(east_north_coordinate_offset_m)
    assert callable(parse_waypoints_file)
    assert callable(sort_clockwise_sweep)
