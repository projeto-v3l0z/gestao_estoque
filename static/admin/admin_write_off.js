$(document).ready(function() {
    var isCreationMode = window.location.href.indexOf('/add/') !== -1;

    function updateFields() {
        if (!isCreationMode) {
            return;
        }
        var locationSelected = $('#id_recomission_storage_type option:selected').text().trim();
        var locationId = locationSelected.val();

        if (locationId) {
            $.ajax({
                url: '/get-storage-type-is-store/',
                data: { 'id': locationId },
                success: function(data) {
                    var isStore = data.is_store;
                    console.log('isStore', isStore);

                    var buildingGroup = $('.field-building');
                    if (isStore) {
                        buildingGroup.show();
                    } else {
                        buildingGroup.hide();
                    }
                    
                    // Adicione lógica adicional para os outros campos (hall, room, shelf) aqui
                },
                error: function() {
                    console.error('Failed to fetch storage type data.');
                }
            });
        }

        var buildingSelected = $('#id_recomission_building').val();
        if (buildingSelected) {
            getBuildingProperties(buildingSelected).then(function(properties) {
                var hallSelected = $('#id_recomission_hall').val();
                var roomSelected = $('#id_recomission_room').val();
                var shelfSelected = $('#id_recomission_shelf').val();

                if (properties.has_hall) {
                    $('.field-recomission_hall').show();
                    updateHalls(buildingSelected, hallSelected);
                } else {
                    $('.field-recomission_hall').hide();
                }

                if (properties.has_room) {
                    $('.field-recomission_room').show();
                    if (hallSelected) {
                        updateRoomsByHall(hallSelected, roomSelected);
                    } else {
                        updateRoomsByBuilding(buildingSelected, roomSelected);
                    }
                } else {
                    $('.field-recomission_room').hide();
                }

                if (properties.has_shelf) {
                    $('.field-recomission_shelf').show();
                    if (roomSelected) {
                        updateShelvesByRoom(roomSelected, shelfSelected);
                    } else if (hallSelected) {
                        updateShelvesByHall(hallSelected, shelfSelected);
                    } else {
                        updateShelvesByBuilding(buildingSelected, shelfSelected);
                    }
                } else {
                    $('.field-recomission_shelf').hide();
                }
            });
        } else {
            $('.field-recomission_hall').hide();
            $('.field-recomission_room').hide();
            $('.field-recomission_shelf').hide();
        }
    }

    function getBuildingProperties(buildingId) {
        return $.ajax({
            url: '/get-building-properties/',
            data: { 'building_id': buildingId }
        });
    }

    function updateHalls(buildingId, selectedHall) {
        if (!buildingId) {
            return;
        }

        $.ajax({
            url: '/get-halls/',
            data: {
                'building_id': buildingId
            },
            success: function(data) {
                $('#id_recomission_hall').empty();
                $('#id_recomission_hall').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedHall) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_recomission_hall').append(option);
                });
            }
        });
    }

    function updateRoomsByBuilding(buildingId, selectedRoom) {
        if (!buildingId) {
            return;
        }

        $.ajax({
            url: '/get-rooms/',
            data: {
                'building_id': buildingId
            },
            success: function(data) {
                $('#id_recomission_room').empty();
                $('#id_recomission_room').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedRoom) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_recomission_room').append(option);
                });
            }
        });
    }

    function updateRoomsByHall(hallId, selectedRoom) {
        if (!hallId) {
            return;
        }

        $.ajax({
            url: '/get-rooms/',
            data: {
                'hall_id': hallId
            },
            success: function(data) {
                $('#id_recomission_room').empty();
                $('#id_recomission_room').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedRoom) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_recomission_room').append(option);
                });
            }
        });
    }

    function updateShelvesByBuilding(buildingId, selectedShelf) {
        if (!buildingId) {
            return;
        }

        $.ajax({
            url: '/get-shelves/',
            data: {
                'building_id': buildingId
            },
            success: function(data) {
                $('#id_recomission_shelf').empty();
                $('#id_recomission_shelf').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedShelf) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_recomission_shelf').append(option);
                });
            }
        });
    }

    function updateShelvesByHall(hallId, selectedShelf) {
        if (!hallId) {
            return;
        }

        $.ajax({
            url: '/get-shelves/',
            data: {
                'hall_id': hallId
            },
            success: function(data) {
                $('#id_recomission_shelf').empty();
                $('#id_recomission_shelf').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedShelf) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_recomission_shelf').append(option);
                });
            }
        });
    }

    function updateShelvesByRoom(roomId, selectedShelf) {
        if (!roomId) {
            return;
        }

        $.ajax({
            url: '/get-shelves/',
            data: {
                'room_id': roomId
            },
            success: function(data) {
                $('#id_recomission_shelf').empty();
                $('#id_recomission_shelf').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedShelf) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_recomission_shelf').append(option);
                });
            }
        });
    }

    $('#id_recomission_storage_type').change(function() {
        updateFields();
    });

    $('#id_recomission_building').change(function() {
        updateFields();
    });

    $('#id_recomission_hall').change(function() {
        updateFields();
    });

    $('#id_recomission_room').change(function() {
        updateFields();
    });

    updateFields();


    
    function updateWriteOffFields() {
        var selectedProductUnit = $('#id_product_unit').val();
        
        if (selectedProductUnit) {
            $.ajax({
                url: '/get-write-off-status/' + selectedProductUnit + '/',
                method: 'GET',
                success: function(data) {
                    var writeOffStatus = data.write_off;
                    if (writeOffStatus === false) {
                        $('.field-storage_type').show();
                        $('.field-write_off_destination').show();
                        $('.field-recomission_storage_type').hide();
                    } else {
                        $('.field-storage_type').hide();
                        $('.field-write_off_destination').hide();
                        $('.field-recomission_storage_type').show();
                    }
                }
            });
        } else {
            $('.field-storage_type').hide();
            $('.field-write_off_destination').hide();
            $('.field-recomission_storage_type').hide();
            $('.field-recomission_building').hide();
            $('.field-recomission_room').hide();
            $('.field-recomission_hall').hide();
            $('.field-recomission_shelf').hide();
        }
    }

    $('#id_product_unit').change(function() {
        updateWriteOffFields();
    });

    updateWriteOffFields();  // Para a inicialização no carregamento da página
});
