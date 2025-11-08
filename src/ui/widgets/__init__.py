"""UI widgets package."""

from .dashboard_widget import DashboardWidget
from .products_widget import ProductsWidget
from .distribution_locations_widget import DistributionLocationsWidget
from .medical_centres_widget import MedicalCentresWidget
from .purchase_orders_widget import PurchaseOrdersWidget
from .coupons_widget import CouponsWidget

__all__ = [
    'DashboardWidget',
    'ProductsWidget',
    'DistributionLocationsWidget',
    'MedicalCentresWidget',
    'PurchaseOrdersWidget',
    'CouponsWidget'
]
