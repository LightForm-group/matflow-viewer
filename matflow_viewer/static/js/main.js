$(document).ready(function () {

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

    // Handle clicking to change task:
    $('.task-wrapper').click(function (evt) {
        var workflowID = $(this).data('wid');
        var taskIdx = $(this).data("task-idx");
        var data = {
            "workflowID": workflowID,
            "taskIdx": taskIdx,
            "elementIdx": 0,
            "inputName": null,
            "outputName": null,
            "fileName": null,
        };
        var newURL = "/workflow/" + workflowID + "/task/" + taskIdx + "/element/0"
        changeTask(data);
        history.pushState(data, "", newURL);
    });

    // Handle clicking to change input/output/file parameter:
    $('.task-inspector').on('click', '.task-param-name', function (event) {

        var paramType = $(this).data('param-type');
        var paramName = $(this).data('param-name');
        var workflowID = $(this).data('wid');
        var taskIdx = $(this).data("task-idx");
        var elementIdx = $('.task-element-button.element-button-active').data("element-idx");

        if ($(this).hasClass('param-name-active')) {
            var data = {
                "workflowID": workflowID,
                "taskIdx": taskIdx,
                "elementIdx": 0,
                "inputName": null,
                "outputName": null,
                "fileName": null,
            };
            var newURL = "/workflow/" + workflowID + "/task/" + taskIdx + "/element/" + elementIdx + "/";
            $('.task-param-name[data-param-name="' + paramName + '"]').removeClass('param-name-active');
        } else {
            var data = {
                "workflowID": workflowID,
                "taskIdx": taskIdx,
                "elementIdx": 0,
                "inputName": $(this).data('param-type') == 'input' ? $(this).data('param-name') : null,
                "outputName": $(this).data('param-type') == 'output' ? $(this).data('param-name') : null,
                "fileName": $(this).data('param-type') == 'file' ? $(this).data('param-name') : null,
            };
            var newURL = "/workflow/" + workflowID + "/task/" + taskIdx + "/element/" + elementIdx + "/" + paramType + "/" + paramName + "/";
            $('.task-param-name').removeClass('param-name-active');
            $('.task-param-name[data-param-name="' + paramName + '"]').addClass('param-name-active');
        }
        changeParameter(data);
        history.pushState(data, "", newURL);
    });

    // Handle clicking to change element:
    $('.task-row').on('click', '.task-element-button', function (evt) {
        var workflowID = $(this).data('wid');
        var taskIdx = $(this).data('task-idx');
        var elementIdx = $(this).data('element-idx');

        var param_name = $('.param-wrapper.param-active').data("param-name");
        var param_type = $('.param-wrapper.param-active').data("param-type");
        var inputName = null;
        var outputName = null;
        var fileName = null;
        if (param_type == 'input') {
            inputName = param_name
        } else if (param_type == 'output') {
            outputName = param_name
        } else if (param_type == 'file') {
            fileName = param_name
        }

        var data = {
            "workflowID": workflowID,
            "taskIdx": taskIdx,
            "elementIdx": elementIdx,
            "inputName": inputName,
            "outputName": outputName,
            "fileName": fileName,
        };
        var newURL = "/workflow/" + workflowID + "/task/" + taskIdx + "/element/" + elementIdx;
        if (param_type) {
            var newURL = newURL + "/" + param_type + "/" + param_name;
        }
        changeElement(data);
        history.pushState(data, "", newURL);
    });


    function updateTask(state) {
        // Compare state.taskIdx, state.elementIdx and state.input/output/fileName, to
        // see what we need to change:
        var currentTaskIdx = $('.task-wrapper.task-active').data("task-idx");
        var currentElementIdx = $('.task-element-button.element-button-active').data("element-idx");

        var param_name = $('.param-wrapper.param-active').data("param-name");
        var param_type = $('.param-wrapper.param-active').data("param-type");
        var currentInputName = null;
        var currentOutputName = null;
        var currentFileName = null;
        if (param_type == 'input') {
            currentInputName = param_name;
        } else if (param_type == 'output') {
            currentOutputName = param_name;
        } else if (param_type == 'file') {
            currentFileName = param_name;
        }

        if (currentTaskIdx != state.taskIdx) {
            console.log("need to change task; sending state: " + state);
            changeTask(state);
        } else if (currentElementIdx != state.elementIdx) {
            console.log("Need to change element; sending state: " + state);
            changeElement(state);
        } else {
            if (currentInputName != state.inputName) {
                console.log("need to change input; sending state: " + state);
            } else if (currentOutputName != state.outputName) {
                console.log("need to change output; sending state: " + state);
            } else if (currentFileName != state.fileName) {
                console.log("need to change file; sending state: " + state);
            }
            changeParameter(state);
        }

    }

    function changeElement(state) {

        var elementIdx = state.elementIdx;
        $('.task-element-button.element-button-active').removeClass('element-button-active');
        $('.task-element-button[data-element-idx=' + elementIdx + ']').addClass('element-button-active');

        $('.task-param-inspector.element-param-active').removeClass('element-param-active');
        $('.task-param-inspector[data-element-idx=' + elementIdx + ']').addClass('element-param-active');

        $('.task-duration.task-duration-active').removeClass('task-duration-active');
        $('.task-duration[data-element-idx="' + elementIdx + '"').addClass('task-duration-active');

        $('.task-resource-use.task-resource-use-active').removeClass('task-resource-use-active');
        $('.task-resource-use[data-element-idx="' + elementIdx + '"').addClass('task-resource-use-active');
    }

    function changeParameter(state) {
        $('.param-wrapper.param-active').removeClass('param-active');
        var paramName = state.inputName || state.outputName || state.fileName
        if (paramName) {
            $('.param-wrapper[data-param-name="' + paramName + '"]').addClass('param-active');
        }


    }

    function changeTask(state) {

        var workflowID = state.workflowID;
        var taskIdx = state.taskIdx;
        var elementIdx = state.elementIdx;

        $('#task-inspector-overlay').addClass('loading');
        $.ajax({
            type: 'POST',
            url: '/get_full_task',
            data: {
                "workflowID": workflowID,
                "taskIdx": taskIdx,
                "elementIdx": elementIdx,
            },
            success: function (response) {
                console.log("success!")
                $('.task-inspector').html(response);
                $('.task-wrapper.task-active').removeClass('task-active');
                $('.task-wrapper[data-task-idx=' + taskIdx + ']').addClass('task-active');
            },
            error: function (error) {
                console.log(error);
            },
            complete: function (data) {
                $('#task-inspector-overlay').removeClass('loading');
            }
        })
        if ($('#task-list-wrapper').hasClass('my-modal')) {
            $('#task-list-wrapper').removeClass('my-modal');
        };
    }

    $(window).on("popstate", function (event) {
        originalState = event.originalEvent.state;
        updateTask(originalState);
    });

    // Store initial state so it can be re-visited:
    var param_name = $('.param-wrapper.param-active').data("param-name");
    var param_type = $('.param-wrapper.param-active').data("param-type");
    var inputName = null;
    var outputName = null;
    var fileName = null;
    if (param_type == 'input') {
        inputName = param_name
    } else if (param_type == 'output') {
        outputName = param_name
    } else if (param_type == 'file') {
        fileName = param_name
    }
    history.replaceState({
        "workflowID": $('#wk-main').data('workflow-id'),
        "taskIdx": $('.task-wrapper.task-active').data("task-idx"),
        "elementIdx": $('.task-element-button.element-button-active').data("element-idx"),
        "inputName": inputName,
        "outputName": outputName,
        "fileName": fileName,
    }, document.title, document.location.href);

});
