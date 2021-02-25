$(document).ready(function() {
    toast_click();
    toast_fade();

    $(".im-date").inputmask({'alias': 'datetime', 'inputFormat': 'dd/MM/yyyy', 'inputMode': 'numeric'});
    $(".im-phone").inputmask("(999) 999-9999");
    // <input data-inputmask-alias="datetime" data-inputmask-inputformat="dd/mm/yyyy" inputmode="numeric">
});

function notify(message, time=4000) {
    let id = `pt-toast-${rand()}`;
    $('.pt-toast').append(`
        <div id="${id}" class="pt-toast-body w-100 rounded p-2 mb-2 position-relative">
            <i class="clear-toast cursor-pointer fas fa-times position-absolute ms-3"></i>
            <div class="text-center gilroy text-white-50">${message}</div>
        </div>
    `);

    $(`#${id}.pt-toast-body`).delay(time).fadeOut(400, function() {
        $(this).remove();
    });
    toast_click();
}

function toast_click() {
    $(".pt-toast .clear-toast").on({
        'click': function() {
            $(this).parents('.pt-toast-body').fadeOut(400, function() {
                $(this).remove();
            });
        }
    });
}

function toast_fade() {
    $.each($(".pt-toast-body"), function(i, e) {
        $(e).delay(4000 + (i*700)).fadeOut(400, function() {
            $(this).remove();
        });
    });
}

function rand(digits=6) {
    let max = '1';
    for (let i = 0; i < digits; i++) {
        max += '0'
    }
    return Math.floor((Math.random()*parseInt(max))+1);
}

$.postJSON = function(url, data, callback) {
  return $.ajax({
    'type': 'POST',
    'url': url,
    'contentType': 'application/json; charset=utf-8',
    'data': JSON.stringify(data),
    'dataType': 'json',
    'success': callback
  });
};