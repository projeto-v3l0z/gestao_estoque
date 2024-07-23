$(document).ready(function() {

    function updateFields() {

        var buildingSelected = $('#id_building').val();
        if (buildingSelected) {
            getBuildingProperties(buildingSelected).then(function(properties) {
                var hallSelected = $('#id_hall').val();
                var roomSelected = $('#id_room').val();
                var shelfSelected = $('#id_shelf').val();

                if (properties.has_hall) {
                    $('.field-hall').show();
                    updateHalls(buildingSelected, hallSelected);
                } else {
                    $('.field-hall').hide();
                }

                if (properties.has_room) {
                    $('.field-room').show();
                    if (hallSelected) {
                        updateRoomsByHall(hallSelected, roomSelected);
                    } else {
                        updateRoomsByBuilding(buildingSelected, roomSelected);
                    }
                } else {
                    $('.field-room').hide();
                }

                if (properties.has_shelf) {
                    $('.field-shelf').show();
                    if (roomSelected) {
                        updateShelvesByRoom(roomSelected, shelfSelected);
                    } else if (hallSelected) {
                        updateShelvesByHall(hallSelected, shelfSelected);
                    } else {
                        updateShelvesByBuilding(buildingSelected, shelfSelected);
                    }
                } else {
                    $('.field-shelf').hide();
                }
            });
        } else {
            $('.field-hall').hide();
            $('.field-room').hide();
            $('.field-shelf').hide();
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
                $('#id_hall').empty();
                $('#id_hall').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedHall) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_hall').append(option);
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
                $('#id_room').empty();
                $('#id_room').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedRoom) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_room').append(option);
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
                $('#id_room').empty();
                $('#id_room').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedRoom) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_room').append(option);
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
                $('#id_shelf').empty();
                $('#id_shelf').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedShelf) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_shelf').append(option);
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
                $('#id_shelf').empty();
                $('#id_shelf').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedShelf) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_shelf').append(option);
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
                $('#id_shelf').empty();
                $('#id_shelf').append($('<option>').text('---------').attr('value', ''));
                $.each(data, function(index, value) {
                    var option = $('<option>').text(value.name).attr('value', value.id);
                    if (value.id == selectedShelf) {
                        option.attr('selected', 'selected');
                    }
                    $('#id_shelf').append(option);
                });
            }
        });
    }

    $('#id_building').change(function() {
        updateFields();
    });

    $('#id_hall').change(function() {
        updateFields();
    });

    $('#id_room').change(function() {
        updateFields();
    });

    updateFields();
});
