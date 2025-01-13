import pytest
import numpy as np
import pandas as pd
from scipy.stats import gamma as gamma_dist
from scipy.special import gammainc

from gwtransport1d.gamma import cout_advection_gamma, gamma_equal_mass_bins, bin_masses


# Fixtures
@pytest.fixture
def sample_time_series():
    """Create sample time series data for testing."""
    dates = pd.date_range(start="2020-01-01", end="2020-12-31", freq="D")
    concentration = pd.Series(np.sin(np.linspace(0, 4 * np.pi, len(dates))) + 2, index=dates)
    flow = pd.Series(np.ones(len(dates)) * 100, index=dates)  # Constant flow of 100 m3/day
    return concentration, flow


@pytest.fixture
def gamma_params():
    """Sample gamma distribution parameters."""
    return {
        "alpha": 2.0,  # Shape parameter
        "beta": 1.0,  # Scale parameter
        "n_bins": 10,  # Number of bins
    }


# Test bin_masses function
def test_bin_masses_basic():
    """Test basic functionality of bin_masses."""
    edges = np.array([0, 1, 2, 3])
    masses = bin_masses(alpha=2.0, beta=1.0, bin_edges=edges)

    assert len(masses) == len(edges) - 1
    assert np.all(masses >= 0)
    assert np.isclose(np.sum(masses), 1.0, rtol=1e-10)


def test_bin_masses_invalid_params():
    """Test bin_masses with invalid parameters."""
    edges = np.array([0, 1, 2])

    with pytest.raises(ValueError):
        bin_masses(alpha=-1, beta=1.0, bin_edges=edges)

    with pytest.raises(ValueError):
        bin_masses(alpha=1.0, beta=-1, bin_edges=edges)


def test_bin_masses_single_bin():
    """Test bin_masses with a single bin."""
    edges = np.array([0, np.inf])
    masses = bin_masses(alpha=2.0, beta=1.0, bin_edges=edges)

    assert len(masses) == 1
    assert np.isclose(masses[0], 1.0, rtol=1e-10)


# Test gamma_equal_mass_bins function
def test_gamma_equal_mass_bins_basic(gamma_params):
    """Test basic functionality of gamma_equal_mass_bins."""
    result = gamma_equal_mass_bins(**gamma_params)

    # Check all required keys are present
    expected_keys = {"lower_bound", "upper_bound", "edges", "expected_value", "probability_mass"}
    assert set(result.keys()) == expected_keys

    # Check array lengths
    n_bins = gamma_params["n_bins"]
    assert len(result["lower_bound"]) == n_bins
    assert len(result["upper_bound"]) == n_bins
    assert len(result["edges"]) == n_bins + 1
    assert len(result["expected_value"]) == n_bins
    assert len(result["probability_mass"]) == n_bins

    # Check probability masses sum to 1
    assert np.isclose(np.sum(result["probability_mass"]), 1.0, rtol=1e-10)

    # Check bin edges are monotonically increasing
    assert np.all(np.diff(result["edges"]) > 0)


def test_gamma_equal_mass_bins_expected_values(gamma_params):
    """Test that expected values are within their respective bins."""
    result = gamma_equal_mass_bins(**gamma_params)

    for i in range(len(result["expected_value"])):
        assert result["lower_bound"][i] <= result["expected_value"][i] <= result["upper_bound"][i]


# Test cout_advection_gamma function
def test_cout_advection_gamma_basic(sample_time_series, gamma_params):
    """Test basic functionality of cout_advection_gamma."""
    cin, flow = sample_time_series

    cout = cout_advection_gamma(
        cin=cin, flow=flow, alpha=gamma_params["alpha"], beta=gamma_params["beta"], n_bins=gamma_params["n_bins"]
    )

    # Check output type and length
    assert isinstance(cout, pd.Series)
    assert len(cout) == len(cin)

    # Check output values are non-negative
    assert np.all(cout >= 0)

    # Check conservation of mass (approximately)
    # Note: This might not hold exactly due to boundary effects
    assert np.isclose(cout.mean(), cin.mean(), rtol=0.1)


def test_cout_advection_gamma_retardation(sample_time_series, gamma_params):
    """Test cout_advection_gamma with different retardation factors."""
    cin, flow = sample_time_series

    # Compare results with different retardation factors
    cout1 = cout_advection_gamma(
        cin=cin, flow=flow, alpha=gamma_params["alpha"], beta=gamma_params["beta"], retardation_factor=1.0
    )

    cout2 = cout_advection_gamma(
        cin=cin, flow=flow, alpha=gamma_params["alpha"], beta=gamma_params["beta"], retardation_factor=2.0
    )

    # The signal with higher retardation should be more delayed
    assert not np.allclose(cout1, cout2)


def test_cout_advection_gamma_constant_input(gamma_params):
    """Test cout_advection_gamma with constant input concentration."""
    # Create constant input concentration
    dates = pd.date_range(start="2020-01-01", end="2020-12-31", freq="D")
    cin = pd.Series(np.ones(len(dates)), index=dates)
    flow = pd.Series(np.ones(len(dates)) * 100, index=dates)

    cout = cout_advection_gamma(cin=cin, flow=flow, alpha=gamma_params["alpha"], beta=gamma_params["beta"])

    # Output should also be constant and equal to input
    assert np.allclose(cout, 1.0, rtol=1e-10)


# Edge cases and error handling
def test_invalid_parameters():
    """Test error handling for invalid parameters."""
    with pytest.raises(ValueError):
        gamma_equal_mass_bins(alpha=-1, beta=1, n_bins=10)

    with pytest.raises(ValueError):
        gamma_equal_mass_bins(alpha=1, beta=-1, n_bins=10)

    with pytest.raises(ValueError):
        gamma_equal_mass_bins(alpha=1, beta=1, n_bins=0)


def test_numerical_stability():
    """Test numerical stability with extreme parameters."""
    # Test with very small alpha and beta
    result_small = gamma_equal_mass_bins(alpha=1e-5, beta=1e-5, n_bins=10)
    assert not np.any(np.isnan(result_small["expected_value"]))

    # Test with very large alpha and beta
    result_large = gamma_equal_mass_bins(alpha=1e5, beta=1e5, n_bins=10)
    assert not np.any(np.isnan(result_large["expected_value"]))