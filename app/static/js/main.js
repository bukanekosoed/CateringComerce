(function ($) {
  "use strict";

  // Spinner
  var spinner = function () {
    setTimeout(function () {
      if ($("#spinner").length > 0) {
        $("#spinner").removeClass("show");
      }
    }, 1);
  };
  spinner(0);

  // Fixed Navbar
  $(window).scroll(function () {
    if ($(window).width() < 992) {
      if ($(this).scrollTop() > 55) {
        $(".fixed-top").addClass("shadow");
      } else {
        $(".fixed-top").removeClass("shadow");
      }
    } else {
      if ($(this).scrollTop() > 55) {
        $(".fixed-top").addClass("shadow").css("top", -55);
      } else {
        $(".fixed-top").removeClass("shadow").css("top", 0);
      }
    }
  });

  // Back to top button
  $(window).scroll(function () {
    if ($(this).scrollTop() > 300) {
      $(".back-to-top").fadeIn("slow");
    } else {
      $(".back-to-top").fadeOut("slow");
    }
  });
  $(".back-to-top").click(function () {
    $("html, body").animate({ scrollTop: 0 }, 1500, "easeInOutExpo");
    return false;
  });

  // Testimonial carousel
  $(".testimonial-carousel").owlCarousel({
    autoplay: true,
    smartSpeed: 2000,
    center: false,
    dots: true,
    loop: true,
    margin: 25,
    nav: true,
    navText: [
      '<i class="bi bi-arrow-left"></i>',
      '<i class="bi bi-arrow-right"></i>',
    ],
    responsiveClass: true,
    responsive: {
      0: {
        items: 1,
      },
      576: {
        items: 1,
      },
      768: {
        items: 1,
      },
      992: {
        items: 2,
      },
      1200: {
        items: 2,
      },
    },
  });

  // vegetable carousel
  $(".vegetable-carousel").owlCarousel({
    autoplay: true,
    smartSpeed: 1500,
    center: false,
    dots: true,
    loop: true,
    margin: 25,
    nav: true,
    navText: [
      '<i class="bi bi-arrow-left"></i>',
      '<i class="bi bi-arrow-right"></i>',
    ],
    responsiveClass: true,
    responsive: {
      0: {
        items: 1,
      },
      576: {
        items: 1,
      },
      768: {
        items: 2,
      },
      992: {
        items: 3,
      },
      1200: {
        items: 4,
      },
    },
  });

  // Modal Video
  $(document).ready(function () {
    var $videoSrc;
    $(".btn-play").click(function () {
      $videoSrc = $(this).data("src");
    });
    console.log($videoSrc);

    $("#videoModal").on("shown.bs.modal", function (e) {
      $("#video").attr(
        "src",
        $videoSrc + "?autoplay=1&amp;modestbranding=1&amp;showinfo=0"
      );
    });

    $("#videoModal").on("hide.bs.modal", function (e) {
      $("#video").attr("src", $videoSrc);
    });
  });

  // Product Quantity
  $(".quantity button").on("click", function () {
    var button = $(this);
    var oldValue = button.parent().parent().find("input").val();
    if (button.hasClass("btn-plus")) {
      var newVal = parseFloat(oldValue) + 1;
    } else {
      if (oldValue > 0) {
        var newVal = parseFloat(oldValue) - 1;
      } else {
        newVal = 0;
      }
    }
    button.parent().parent().find("input").val(newVal);
  });
})(jQuery);

function formatCurrency(value) {
  let formatted = value.toLocaleString("id-ID", {
    style: "currency",
    currency: "IDR",
  });
  return formatted.replace(/,00$/, "");
}

$(
  "form[id^='form_decrement_'], form[id^='form_update_'], form[id^='form_increment_']"
).on("submit", function (event) {
  event.preventDefault(); // Prevent default form submission

  var form = $(this);
  var action = form.find('input[name="action"]').val();
  var formId = form.attr("id");
  var productId = formId.split("_")[2]; // Extract product ID from form ID

  $.ajax({
    url: form.attr("action"),
    method: "POST",
    data: form.serialize(),
    success: function (response) {
      if (response.error) {
        alert(response.error);
        return;
      }

      // Update product total cost and quantities
      $("#total_" + productId).text(
        "Total: " + formatCurrency(response.total_cost)
      );
      $("#quantity_" + productId).val(response.quantity);

      // Update totals and costs
      $("#grandTotal").text(formatCurrency(response.grand_total));
      $("#ppnCost").text(formatCurrency(response.ppn_cost));
      $("#subtotal").text(formatCurrency(response.total_price));
      $("#shipmentCost").text(formatCurrency(response.shipment_cost)); // Added for shipment cost

      // Update button states
      $("#form_decrement_" + productId + " button").prop(
        "disabled",
        response.quantity <= response.minPembelian
      );
      $("#form_increment_" + productId + " button").prop("disabled", false);
    },
    error: function (xhr) {
      alert("An error occurred: " + xhr.responseText);
    },
  });
});


$('input[name="delivery_option"]').on("change", function () {
  var deliveryOption = $(this).val();
  if (deliveryOption === "delivery") {
    $("#address-selection").show();
  } else {
    $("#address-selection").hide();
  }
  updateDeliveryOption();
});

$("#address-select").on("change", function () {
  updateDeliveryOption();
});

function updateDeliveryOption() {
  var deliveryOption = $('input[name="delivery_option"]:checked').val();
  var addressIndex = $("#address-select").val();

  $.ajax({
    url: "/update_delivery_option",
    type: "POST",
    data: {
      delivery_option: deliveryOption,
      address_index: addressIndex,
    },
    success: function (response) {
      $("#shippingCost").text(formatCurrency(response.shipping_cost));
      $("#grandTotal").text(formatCurrency(response.grand_total));
    },
  });
}

// Initialize address selection display
if ($('input[name="delivery_option"]:checked').val() === "delivery") {
  $("#address-selection").show();
}

// profile dropdown
$(document).ready(function () {
  $('#profileDropdown').hover(
    function () {
      $('.profileDropdown').stop(true, true).fadeIn(200); // Tampilkan dropdown saat hover
      adjustDropdownPosition(); // Sesuaikan posisi dropdown
    },
    function () {
      $('.profileDropdown').stop(true, true).fadeOut(200); // Sembunyikan dropdown saat tidak hover
    }
  );

  $('.profileDropdown').hover(
    function () {
      $(this).stop(true, true).fadeIn(200); // Tetap tampilkan saat hover di dropdown
    },
    function () {
      $(this).stop(true, true).fadeOut(200); // Sembunyikan saat mouse keluar
    }
  );

  function adjustDropdownPosition() {
    const dropdown = $('.profileDropdown');
    const offset = dropdown.offset();
    const windowHeight = $(window).height();

    // Jika dropdown melebihi batas bawah viewport
    if (offset.top + dropdown.outerHeight() > windowHeight) {
      dropdown.css({ top: 'auto', bottom: '100%', left: '-100px' }); // Tampilkan di atas
    } else {
      dropdown.css({ top: '100%', bottom: 'auto', left: '-100px' }); // Tampilkan di bawah
    }
  }
});

// cart dropdown
$(document).ready(function () {
  $('#cartDropdown').hover(
    function () {
      $('.cartDropdown').stop(true, true).fadeIn(200); // Tampilkan dropdown saat hover
      adjustDropdownPosition(); // Sesuaikan posisi dropdown
    },
    function () {
      $('.cartDropdown').stop(true, true).fadeOut(200); // Sembunyikan dropdown saat tidak hover
    }
  );

  $('.cartDropdown').hover(
    function () {
      $(this).stop(true, true).fadeIn(200); // Tetap tampilkan saat hover di dropdown
    },
    function () {
      $(this).stop(true, true).fadeOut(200); // Sembunyikan saat mouse keluar
    }
  );

  function adjustDropdownPosition() {
    const dropdown = $('.cartDropdown');
    const offset = dropdown.offset();
    const windowHeight = $(window).height();

    // Jika dropdown melebihi batas bawah viewport
    if (offset.top + dropdown.outerHeight() > windowHeight) {
      dropdown.css({ top: 'auto', bottom: '100%', left: '-100px' }); // Tampilkan di atas
    } else {
      dropdown.css({ top: '100%', bottom: 'auto', left: '-100px' }); // Tampilkan di bawah
    }
  }
  
});

