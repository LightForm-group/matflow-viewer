$(document).ready(function () {

    $('.task-inspector').on('click', '.task-param-name', function (event) {

        var param_name = $(this).data('param-name');
        var param_type = $(this).data('param-type');
        var elems = $('.task-param-name[data-param-name="' + param_name + '"]');
        var other_elems = $('.task-file-name');

        if ($(this).hasClass('active')) {
            $('#param-wrapper').html('');
            elems.removeClass('active');
        }
        else {
            var task_idx = $(this).data('task-idx');
            var wid = $(this).data('wid');
            var element_idx = $(this).data('element-idx');
            $.ajax({
                type: 'POST',
                url: '/get_param',
                data: {
                    "wid": wid,
                    "task_idx": task_idx,
                    "element_idx": element_idx,
                    "param_name": param_name,
                    "param_type": param_type,
                },
                success: function (response) {
                    $('#param-wrapper').html(response);
                    $('.task-param-name.active').removeClass('active');
                    elems.addClass('active');
                    other_elems.removeClass('active');
                },
                error: function (error) {
                    console.log(error);
                }
            });
        }
    });

    $('.task-inspector').on('click', '.task-file-name', function (event) {

        var file_name = $(this).data('file-name');
        var elems = $('.task-file-name[data-file-name="' + file_name + '"]');
        var other_elems = $('.task-param-name');

        if ($(this).hasClass('active')) {
            $('#param-wrapper').html('');
            elems.removeClass('active');
        }
        else {
            var task_idx = $(this).data('task-idx');
            var wid = $(this).data('wid');
            var element_idx = $(this).data('element-idx');
            var file_location = $(this).data('file-location');
            $.ajax({
                type: 'POST',
                url: '/get_file',
                data: {
                    "wid": wid,
                    "task_idx": task_idx,
                    "element_idx": element_idx,
                    "file_name": file_name,
                    "file_location": file_location,
                },
                success: function (response) {
                    $('#param-wrapper').html(response);
                    $('.task-file-name.active').removeClass('active');
                    elems.addClass('active');
                    other_elems.removeClass('active');
                },
                error: function (error) {
                    console.log(error);
                }
            });
        }
    });

    $(document).click(function (evt) {

        if (evt.target.id == "all-tasks-button") {
            $('#task-list-wrapper').toggleClass('my-modal');
            return;
        }

        if ($('#task-list-wrapper').hasClass('my-modal')) {

            if (evt.target.id == "task-list-wrapper")
                return;

            $('#task-list-wrapper').toggleClass('my-modal');

        };
    });

    $('.task-wrapper').click(function (evt) {
        var task_idx = $(this).data('task-idx');
        var wid = $(this).data('wid');
        var elem = $(this);
        $.ajax({
            type: 'POST',
            url: '/get_task',
            data: {
                "wid": wid,
                "task_idx": task_idx,
                "element_idx": 0,
            },
            success: function (response) {
                $('.task-inspector').html(response);
                $('.task-wrapper.task-active').removeClass('task-active').addClass('task-inactive');
                elem.removeClass('task-inactive');
                elem.addClass('task-active');
            },
            error: function (error) {
                console.log(error);
            }
        })
        if ($('#task-list-wrapper').hasClass('my-modal')) {
            $('#task-list-wrapper').removeClass('my-modal');
        };
    });

    $('.task-row').on('click', '.task-element-button', function (evt) {
        var task_idx = $(this).data('task-idx');
        var wid = $(this).data('wid');
        var element_idx = $(this).data('element-idx')
        $.ajax({
            type: 'POST',
            url: '/get_task',
            data: {
                "wid": wid,
                "task_idx": task_idx,
                "element_idx": element_idx,
            },
            success: function (response) {
                $('.task-inspector').html(response);
            },
            error: function (error) {
                console.log(error);
            }
        })
    });

});
