
JAZZMIN_SETTINGS = {
    "welcome_sign": "Bem-vindo ao painel de administração",
    "site_header": "Administração",
    "hide_models": ["inventory_management.room"],
    "changeform_format": "single",
    "topmenu_links": [
        {"name": "Home",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Produtos", "url": "admin:inventory_management_product_changelist", "permissions": ["inventory_management.view_product"]},
        {"name": "Unidades de Produto", "url": "admin:inventory_management_productunit_changelist", "permissions": ["inventory_management.view_productunit"]},
        {"name": "Transferências", "url": "admin:inventory_management_stockTransfer_changelist", "permissions": ["inventory_management.view_stockTransfer"]},
        {"name": "Carregar Dados do Excel", "url": "inventory_management:load_data", "permissions": ["auth.is_superuser"]}, 
        {"name": "Voltar para o site", "url": "/"},
    ],


    "order_with_respect_to": [
        "inventory_management",
        "inventory_management.product",
        "inventory_management.productunit",
        "inventory_management.stocktransfer",
        "inventory_management.write_off",
        "inventory_management.building",
        "inventory_management.hall",
        "inventory_management.shelf",
        "inventory_management.color",
        "inventory_management.pattern",
        "inventory_management.WriteOffDestinations",
        "inventory_management.TransferAreas",
        "inventory_management.WorkSpace",

        "auth",
        "auth.user",
        "auth.group"
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "inventory_management": "fas fa-boxes",
        "inventory_management.product": "fas fa-box-open",
        "inventory_management.stocktransfer": "fas fa-exchange-alt",
        "inventory_management.productunit": "fas fa-cube",
        "inventory_management.building": "fas fa-building",
        "inventory_management.hall": "fas fa-door-open",
        "inventory_management.shelf": "fas fa-box",
        "inventory_management.color": "fas fa-palette",
        "inventory_management.pattern": "fas fa-scroll",
        "inventory_management.write_off": "fa fa-arrow-circle-down",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}