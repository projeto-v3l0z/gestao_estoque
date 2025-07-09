from django.urls import path
from .views import *
from . import views

app_name = 'inventory_management'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('produtos/', ProductListView.as_view(), name='product_list'),
    path('unidades/', ProductUnitListView.as_view(), name='product_unit_list'),
    path('produto/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('produto/<slug:product_slug>/unidade/<slug:slug>/', ProductUnitDetailView.as_view(), name='product_unit_detail'),
    path('produto/', ProductCreateView.as_view(), name='product_create'),
    path('produtos/editarprodutos/<uuid:product_id>/', ProductUpdateView.as_view(), name = 'product_edit'),
    path('escanearQR/', ScanQRView.as_view(), name='scan_qr'),
    path('sobre/', AboutView.as_view(), name='about'),
    path('enderecos/', AdressesView.as_view(), name='adresses'),
    path('enderecos/<slug:slug>/', AddressDetailView.as_view(), name='address_detail'),
    path('get-product-location-shelf/<uuid:product_unit_id>/', GetProductLocationShelfView.as_view(), name='get_product_location_shelf'),  path('generate_qr_codes', views.generate_qr_codes, name='generate_qr_codes'),

    path('area_trabalho/', WorkSpaceView.as_view(), name='workspace'),
    path('area_trabalho/<str:code>/delete/', delete_workspace, name='delete_workspace'),
    
    path('area-trabalho-baixado/', WorkSpaceWriteOffView.as_view(), name='workspace_write_off'),
    path('area-trabalho-baixado/<str:code>/delete/', delete_workspace_write_off, name='delete_workspace_write_off'),
    path('recomissionar/', recomission_product_units, name='recomission'),

    path('area-trabalho-dividido/', WorkSpaceDividedView.as_view(), name='workspace_divided'),
    path('informacoes-unidade-produto/<str:product_unit_id>/', get_product_unit_info, name='product_unit_info'),

    path('get-building-properties/', views.get_building_properties, name='get_building_properties'),
    path('get-rooms/', views.get_rooms, name='get_rooms'),
    path('get-halls/', views.get_halls, name='get_halls'),
    path('get-shelves/', views.get_shelves, name='get_shelves'),
    path('get-write-off-status/<uuid:product_unit_id>/', get_write_off_status, name='get_write_off_status'),
    path('get-storage-type-is-store/', get_storage_type_is_store, name='get_storage_type_is_store'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('carregar-dados/', UploadExcelView.as_view(), name='load_data'),
    path('logout/', logout_view, name='logout'),
    
    path('product-unit/create/', ProductUnitCreateView.as_view(), name='product_unit_create'),
    # path('product-unit/update/<uuid:pk>/', ProductUnitUpdateView.as_view(), name='product_unit_update'),
    path('product-autocomplete/', ProductAutoComplete.as_view(), name='product-autocomplete'),

    # qr code unidade de produto
    path('unidades/qr-code', generate_product_unit_qr_codes, name='generate_product_unit_qr_code'),
]
