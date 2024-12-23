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
  function startProgressBarAndRemoveAlert(alertElement) {
    var progressBar = alertElement.find('.progress-bar');
    progressBar.css('width', '100%');

    setTimeout(function () {
      alertElement.alert('close');
    }, 2000);
  }


  $('.alert').each(function () {
    startProgressBarAndRemoveAlert($(this));
  });
  
  $('#profileDropdown').hover(
    function () {
      $('.profileDropdown').stop(true, true).fadeIn(200); // Tampilkan dropdown saat hover
      adjustDropdownPosition(); // Sesuaikan posisi dropdown jika diperlukan
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
      dropdown.css({ top: '100%', bottom: 'auto%', left: '-100px' }); // Tampilkan di atas
    } else {
      dropdown.css({ top: '100%', bottom: 'auto', left: '-100px' }); // Tampilkan di bawah
    }
  }

  const map = L.map('map').setView([-6.876916, 109.047849], 10);

  // Load the HD tile layer from Thunderforest
  L.tileLayer('https://tile.thunderforest.com/atlas/{z}/{x}/{y}@2x.png?apikey=6aa02e5af5274e7abd8736a2f111edde', {
    maxZoom: 20,
    attribution: '&copy; <a href="https://tile.thunderforest.com/">Thunderforest</a>',
    tileSize: 512,
    zoomOffset: -1,
  }).addTo(map);

  let marker;

  function getLocation() {
    if (navigator.geolocation) {
      navigator.permissions.query({ name: 'geolocation' }).then(function (permissionStatus) {
        if (permissionStatus.state === 'granted' || permissionStatus.state === 'prompt') {
          navigator.geolocation.getCurrentPosition(showPosition, showError);
        } else {
          alert('Geolocation access has been denied. Please allow location access in your browser settings.');
        }

        permissionStatus.onchange = function () {
          if (this.state === 'granted') {
            navigator.geolocation.getCurrentPosition(showPosition, showError);
          } else if (this.state === 'denied') {
            alert('Geolocation access has been denied. Please allow location access in your browser settings.');
          }
        };
      });
    } else {
      alert('Geolocation is not supported by this browser.');
    }
  }

  function showPosition(position) {
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;

    map.setView([lat, lng], 17);

    if (marker) {
      marker.setLatLng([lat, lng]).update();
    } else {
      marker = L.marker([lat, lng], { draggable: true }).addTo(map)
        .bindPopup('Lokasi Anda Sekarang')
        .openPopup();
    }

    updateCoordinates(lat, lng);

    marker.on('dragend', function (e) {
      const { lat, lng } = e.target.getLatLng();
      updateCoordinates(lat, lng);
    });
  }

  function showError(error) {
    switch (error.code) {
      case error.PERMISSION_DENIED:
        alert('User denied the request for Geolocation.');
        break;
      case error.POSITION_UNAVAILABLE:
        alert('Location information is unavailable.');
        break;
      case error.TIMEOUT:
        alert('The request to get user location timed out.');
        break;
      case error.UNKNOWN_ERROR:
        alert('An unknown error occurred.');
        break;
    }
  }

  function updateCoordinates(lat, lng) {
    document.getElementById('latitude').value = lat;
    document.getElementById('longitude').value = lng;

    // Check distance from default location
    checkDistance(lat, lng);

    // Update city (kota) field based on coordinates
    updateAddressFields(lat, lng);
  }

  function updateAddressFields(lat, lng) {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&addressdetails=1`;

    fetch(url)
      .then(response => response.json())
      .then(data => {
        const address = data.address;
        if (address) {
          document.getElementById('district').value = address.city || address.county || '';
          document.getElementById('sub_district').value = address.city || address.county || '';
        }
      })
      .catch(error => console.error('Error:', error));
  }

  function checkDistance(lat, lng) {
    const defaultLat = -6.876916;
    const defaultLng = 109.047849;
    const url = `https://router.project-osrm.org/route/v1/driving/${defaultLng},${defaultLat};${lng},${lat}?overview=false`;

    fetch(url)
      .then(response => response.json())
      .then(data => {
        const distance = data.routes[0].distance; // Distance in meters
        const distanceInKm = distance / 1000;

        const saveButton = document.getElementById('saveAddressButton');

        if (distanceInKm > 70) {
          saveButton.disabled = true;
          saveButton.classList.add('btn-secondary'); // Optional: Change button style to indicate it's disabled
          alert('Jarak dari lokasi toko lebih dari 70 km. Alamat tidak dapat disimpan.');
        } else {
          saveButton.disabled = false;
          saveButton.classList.remove('btn-secondary'); // Optional: Restore original button style
        }
      })
      .catch(error => console.error('Error:', error));
  }

  map.on('click', function (e) {
    const { lat, lng } = e.latlng;

    if (marker) {
      marker.setLatLng([lat, lng]).update();
    } else {
      marker = L.marker([lat, lng], { draggable: true }).addTo(map)
        .bindPopup('Lokasi Anda Sekarang')
        .openPopup();

      marker.on('dragend', function (e) {
        const { lat, lng } = e.target.getLatLng();
        updateCoordinates(lat, lng);
      });
    }

    updateCoordinates(lat, lng);
  });

  document.getElementById('addAddressModal').addEventListener('shown.bs.modal', function () {
    map.invalidateSize();
    getLocation();
  });

  // Mendapatkan tanggal saat ini
  const today = new Date();
  today.setDate(today.getDate() + 3);
  const dd = String(today.getDate()).padStart(2, '0');
  const mm = String(today.getMonth() + 1).padStart(2, '0');
  const yyyy = today.getFullYear();
  const minDate = `${yyyy}-${mm}-${dd}`;

  // Set atribut min pada input date
  const deliveryDateInput = document.getElementById('delivery-date');
  const deliveryTimeInput = document.getElementById('delivery-time');

  // Disable input waktu di awal
  deliveryTimeInput.disabled = true;

  deliveryDateInput.setAttribute('min', minDate);

  // Validasi input tanggal saat field kehilangan fokus (blur)
  function validateDate() {
    const selectedDate = new Date(deliveryDateInput.value);
    const currentDate = new Date();
    currentDate.setDate(currentDate.getDate() + 3); // 3 hari ke depan

    // Validasi setelah tanggal dipilih
    if (deliveryDateInput.value) {
      if (selectedDate < currentDate) {
        alert("Tanggal pengiriman harus lebih dari atau sama dengan 3 hari dari hari ini.");
        deliveryDateInput.value = ''; // Reset input tanggal
        deliveryTimeInput.disabled = true; // Disable kembali waktu jika tanggal tidak valid
      } else {
        // Enable input waktu jika tanggal valid
        deliveryTimeInput.disabled = false;
      }
    }
  }

  // Validasi input waktu saat field kehilangan fokus (blur)
  function validateTime() {
    const timeValue = deliveryTimeInput.value;

    if (timeValue) {
      const [hours, minutes] = timeValue.split(':').map(Number);
      if ((hours < 6 || hours > 19)) {
        alert("Waktu Pengiriman Hanya Pada 06:00 Sampai 19:00");
        deliveryTimeInput.value = ''; // Reset input waktu
      }
    }
  }

  // Event listeners untuk validasi saat input kehilangan fokus (blur)
  deliveryDateInput.addEventListener('blur', validateDate);
  deliveryTimeInput.addEventListener('blur', validateTime);


});

// cart dropdown
$(document).ready(function () {
  $('#cartDropdown').hover(
    function () {
      $('.cartDropdown').stop(true, true).fadeIn(200); // Show dropdown on hover
      adjustDropdownPosition(); // Adjust dropdown position dynamically
    },
    function () {
      $('.cartDropdown').stop(true, true).fadeOut(200); // Hide dropdown when not hovering
    }
  );

  $('.cartDropdown').hover(
    function () {
      $(this).stop(true, true).fadeIn(200); // Keep dropdown visible when hovering over it
    },
    function () {
      $(this).stop(true, true).fadeOut(200); // Hide when mouse leaves dropdown
    }
  );

  function adjustDropdownPosition() {
    const dropdown = $('.cartDropdown');
    const offset = dropdown.offset();
    const windowHeight = $(window).height();

    // If the dropdown exceeds the viewport's bottom edge
    if (offset.top + dropdown.outerHeight() > windowHeight) {
      dropdown.css({ top: '100%', bottom: 'auto', left: '-180px' }); // Display above
    } else {
      dropdown.css({ top: '100%', bottom: 'auto', left: '-180px' }); // Display below
    }
  }

  function checkDateTimeFilled() {
    var deliveryDate = $('#delivery-date').val();
    var deliveryTime = $('#delivery-time').val();

    if (deliveryDate && deliveryTime) {
      // Enable checkout button if both date and time are filled
      $('#checkoutButton').prop('disabled', false);
    } else {
      // Disable checkout button if either field is empty
      $('#checkoutButton').prop('disabled', true);
    }
  }

  // Attach event listeners to detect changes in date and time inputs
  $('#delivery-date, #delivery-time').on('change', function () {
    checkDateTimeFilled();
  });


  const map = L.map('map').setView([-6.876916, 109.047849], 10);

  // Load the HD tile layer from Thunderforest
  L.tileLayer('https://tile.thunderforest.com/atlas/{z}/{x}/{y}@2x.png?apikey=6aa02e5af5274e7abd8736a2f111edde', {
    maxZoom: 20,
    attribution: '&copy; <a href="https://tile.thunderforest.com/">Thunderforest</a>',
    tileSize: 512,
    zoomOffset: -1,
  }).addTo(map);

  let marker;

  function getLocation() {
    if (navigator.geolocation) {
      navigator.permissions.query({ name: 'geolocation' }).then(function (permissionStatus) {
        if (permissionStatus.state === 'granted' || permissionStatus.state === 'prompt') {
          navigator.geolocation.getCurrentPosition(showPosition, showError);
        } else {
          alert('Geolocation access has been denied. Please allow location access in your browser settings.');
        }

        permissionStatus.onchange = function () {
          if (this.state === 'granted') {
            navigator.geolocation.getCurrentPosition(showPosition, showError);
          } else if (this.state === 'denied') {
            alert('Geolocation access has been denied. Please allow location access in your browser settings.');
          }
        };
      });
    } else {
      alert('Geolocation is not supported by this browser.');
    }
  }

  function showPosition(position) {
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;

    map.setView([lat, lng], 17);

    if (marker) {
      marker.setLatLng([lat, lng]).update();
    } else {
      marker = L.marker([lat, lng], { draggable: true }).addTo(map)
        .bindPopup('Lokasi Anda Sekarang')
        .openPopup();
    }

    updateCoordinates(lat, lng);

    marker.on('dragend', function (e) {
      const { lat, lng } = e.target.getLatLng();
      updateCoordinates(lat, lng);
    });
  }

  function showError(error) {
    switch (error.code) {
      case error.PERMISSION_DENIED:
        alert('User denied the request for Geolocation.');
        break;
      case error.POSITION_UNAVAILABLE:
        alert('Location information is unavailable.');
        break;
      case error.TIMEOUT:
        alert('The request to get user location timed out.');
        break;
      case error.UNKNOWN_ERROR:
        alert('An unknown error occurred.');
        break;
    }
  }

  function updateCoordinates(lat, lng) {
    document.getElementById('latitude').value = lat;
    document.getElementById('longitude').value = lng;

    // Check distance from default location
    checkDistance(lat, lng);

    // Update city (kota) field based on coordinates
    updateAddressFields(lat, lng);
  }

  function updateAddressFields(lat, lng) {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&addressdetails=1`;

    fetch(url)
      .then(response => response.json())
      .then(data => {
        const address = data.address;
        if (address) {
          document.getElementById('district').value = address.city || address.county || '';

        }
      })
      .catch(error => console.error('Error:', error));
  }

  function checkDistance(lat, lng) {
    const defaultLat = -6.876916;
    const defaultLng = 109.047849;
    const url = `https://router.project-osrm.org/route/v1/driving/${defaultLng},${defaultLat};${lng},${lat}?overview=false`;

    fetch(url)
      .then(response => response.json())
      .then(data => {
        const distance = data.routes[0].distance; // Distance in meters
        const distanceInKm = distance / 1000;

        const saveButton = document.getElementById('saveAddressButton');

        if (distanceInKm > 40) {
          saveButton.disabled = true;
          saveButton.classList.add('btn-secondary'); // Optional: Change button style to indicate it's disabled
          alert('Jarak dari lokasi toko lebih dari 70 km. Alamat tidak dapat disimpan.');
        } else {
          saveButton.disabled = false;
          saveButton.classList.remove('btn-secondary'); // Optional: Restore original button style
        }
      })
      .catch(error => console.error('Error:', error));
  }

  map.on('click', function (e) {
    const { lat, lng } = e.latlng;

    if (marker) {
      marker.setLatLng([lat, lng]).update();
    } else {
      marker = L.marker([lat, lng], { draggable: true }).addTo(map)
        .bindPopup('Lokasi Anda Sekarang')
        .openPopup();

      marker.on('dragend', function (e) {
        const { lat, lng } = e.target.getLatLng();
        updateCoordinates(lat, lng);
      });
    }

    updateCoordinates(lat, lng);
  });

  document.getElementById('addAddressModal').addEventListener('shown.bs.modal', function () {
    map.invalidateSize();
    getLocation();
  });
});

