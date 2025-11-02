"""
A program to fit a RandomForestClassifier on the digits dataset.

Example invocations:
    python examples/digits.py
    python examples/digits.py --n_estimators 50 -q -o out.txt
"""

# Import datasets, classifiers and performance metrics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from sklearn import datasets, metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from startle import start


@dataclass
class RandomForestConfig:
    """
    Configuration for the RandomForestClassifier.

    Attributes:
        n_estimators: The number of trees in the forest.
        criterion: The function to measure the quality of a split.
        max_depth: The maximum depth of the tree.
    """

    n_estimators: int = 100
    criterion: Literal["gini", "entropy", "log_loss"] = "gini"
    max_depth: int | None = None


@dataclass
class DatasetConfig:
    """
    Configuration for the dataset split.

    Attributes:
        test_size: The proportion of the dataset to include in the test split.
        shuffle: Whether or not to shuffle the data before splitting.
    """

    test_size: float = 0.5
    shuffle: bool = True


def fit_rf(
    model_config: RandomForestConfig,
    dataset_config: DatasetConfig,
    *,
    quiet: bool = False,
    output_file: Path | None = None,
):
    """
    Fit a RandomForestClassifier on the digits dataset and print the classification report.

    Args:
        model_config: Configuration for the RandomForestClassifier.
        dataset_config: Configuration for the dataset split.
        quiet: If True, suppress output.
        output_file: Optional path to save the output.
    """

    digits = datasets.load_digits()

    n_samples = len(digits.images)
    data = digits.images.reshape((n_samples, -1))

    clf = RandomForestClassifier(**asdict(model_config))

    X_train, X_test, y_train, y_test = train_test_split(
        data, digits.target, **asdict(dataset_config)
    )

    clf.fit(X_train, y_train)

    predicted = clf.predict(X_test)
    report = metrics.classification_report(y_test, predicted)

    if not quiet:
        print(report)
    if output_file is not None:
        with open(output_file, "w") as f:
            f.write(report)


if __name__ == "__main__":
    start(fit_rf, recurse=True, catch=False)
