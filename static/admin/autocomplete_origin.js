$(document).ready(function() {
    $('#id_product_unit').change(function() {
        var selectedProductUnit = $(this).val();
        if (selectedProductUnit) {
            $.ajax({
                url: '/get-product-location-shelf/' + selectedProductUnit + '/',
                success: function(data) {
                    console.log("Received data:", data);
                    $('#id_origin_storage_type').val(data.location).trigger('change');
                    $('#id_origin_building').val(data.building).trigger('change');
                    $('#id_origin_hall').val(data.hall).trigger('change');
                    $('#id_origin_room').val(data.room).trigger('change');
                    $('#id_origin_shelf').val(data.shelf).trigger('change');

                    updateFields(data.location);
                },
                error: function(xhr, status, error) {
                    console.error("Error fetching data:", status, error);
                }
            });
        }
    });

    var isCreationMode = window.location.href.indexOf('/add/') !== -1;

    function updateFields(storageTypeId) {
        if (!isCreationMode) {
            return;
        }
        $('.field-destination_building').hide();
        if (storageTypeId) {
            $.ajax({
                url: '/get-storage-type-is-store/',
                data: { 'id': storageTypeId },
                success: function(data) {
                    var isStore = data.is_store;

                    if (isStore) {
                        $('.field-destination_building').show();
                    } 
                        
                

                    var buildingSelected = $('#id_destination_building').val();
                    if (buildingSelected) {
                        getBuildingProperties(buildingSelected).then(function(properties) {
                            var hallSelected = $('#id_destination_hall').val();
                            var roomSelected = $('#id_destination_room').val();
                            var shelfSelected = $('#id_destination_shelf').val();

                            if (properties.has_hall) {
                                $('.field-destination_hall').show();
                                updateHalls(buildingSelected, hallSelected);
                            } else {
                                $('.field-destination_hall').hide();
                            }

                            if (properties.has_room) {
                                $('.field-destination_room').show();
                                if (hallSelected) {
                                    updateRoomsByHall(hallSelected, roomSelected);
                                } else {
                                    updateRoomsByBuilding(buildingSelected, roomSelected);
                                }
                            } else {
                                $('.field-destination_room').hide();
                            }

                            if (properties.has_shelf) {
                                $('.field-destination_shelf').show();
                                if (roomSelected) {
                                    updateShelvesByRoom(roomSelected, shelfSelected);
                                } else if (hallSelected) {
                                    updateShelvesByHall(hallSelected, shelfSelected);
                                } else {
                                    updateShelvesByBuilding(buildingSelected, shelfSelected);
                                }
                            } else {
                                $('.field-destination_shelf').hide();
                            }
                        });
                    } else {
                        $('.field-destination_hall').hide();
                        $('.field-destination_room').hide();
                        $('.field-destination_shelf').hide();
                    }
                },
                error: function() {
                    console.error('Failed to fetch storage type data.');
                }
            });
        } else {
            $('.field-destination_hall').hide();
            $('.field-destination_room').hide();
            $('.field-destination_shelf').hide();
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
                $('#id_destination_hall').empty();
                $('#id_destination_hall').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedHall) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_destination_hall').append(option);
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
                $('#id_destination_room').empty();
                $('#id_destination_room').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedRoom) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_destination_room').append(option);
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
                $('#id_destination_room').empty();
                $('#id_destination_room').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedRoom) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_destination_room').append(option);
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
                $('#id_destination_shelf').empty();
                $('#id_destination_shelf').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedShelf) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_destination_shelf').append(option);
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
                $('#id_destination_shelf').empty();
                $('#id_destination_shelf').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedShelf) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_destination_shelf').append(option);
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
                $('#id_destination_shelf').empty();
                $('#id_destination_shelf').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedShelf) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_destination_shelf').append(option);
                });
            }
        });
    }

    $('#id_destination_storage_type').change(function() {
        updateFields($('#id_destination_storage_type').val());
    });

    $('#id_destination_building').change(function() {
        updateFields($('#id_destination_storage_type').val());
    });

    $('#id_destination_hall').change(function() {
        updateFields($('#id_destination_storage_type').val());
    });

    $('#id_destination_room').change(function() {
        updateFields($('#id_destination_storage_type').val());
    });

    // Initialize fields based on the current value of the storage type
    updateFields($('#id_destination_storage_type').val());
});
