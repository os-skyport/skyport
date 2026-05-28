from pathlib import Path

from core.models import PassengerClass
from data_io.parser import load_passengers


def test_whitespace_input_normalizes_ids_and_numeric_classes():
    passengers = load_passengers("input.txt")

    assert passengers[0].passenger_id == "P01"
    assert passengers[0].cls is PassengerClass.ECONOMY


def test_csv_input_with_comments(tmp_path: Path):
    path = tmp_path / "passengers.csv"
    path.write_text(
        "# comment\n"
        "passenger_id,arrival_time,class,service_time\n"
        "7,5,first,15\n",
        encoding="utf-8",
    )

    passengers = load_passengers(path)

    assert passengers[0].passenger_id == "P07"
    assert passengers[0].cls is PassengerClass.FIRST
    assert passengers[0].service_time == 15
