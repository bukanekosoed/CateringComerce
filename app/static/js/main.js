$(document).ready(function () {
  "use strict";

  // Spinner
  var spinner = function () {
    setTimeout(function () {
      if ($("#spinner").length > 0) {
        $("#spinner").removeClass("show");
      }
    }, 1);
  };
  spinner();



  function formatCurrency(value) {
    
    let formatted = value.toLocaleString("id-ID", {
        style: "currency",
        currency: "IDR",
        minimumFractionDigits: 0,  
        maximumFractionDigits: 0   
    });

    return formatted;
}


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
        $("#grandTotal h5:last").text(formatCurrency(response.grand_total));
      },
    });
  }

  // Initialize address selection display
  if ($('input[name="delivery_option"]:checked').val() === "delivery") {
    $("#address-selection").show();
  }

  function startProgressBarAndRemoveAlert(alertElement) {
    var progressBar = alertElement.find('.progress-bar');
    progressBar.css('width', '100%');

    setTimeout(function () {
      alertElement.alert('close');
    }, 2000);
  }

  $("#inputPassword, #inputConfirmPassword").on("input", function () {
    const password = $("#inputPassword").val();
    const confirmPassword = $("#inputConfirmPassword").val();

    if (password && confirmPassword && password !== confirmPassword) {
      $("#passwordError").fadeIn();
    } else {
      $("#passwordError").fadeOut();
    }
  });


  // Hint Nama
  $('#name').on('input', function () {
    const name = $(this).val();
    const validName = /^[A-Za-z\s]+$/;

    if (!validName.test(name)) {
      $('#nameHelp').show();
    } else {
      $('#nameHelp').hide();
    }
  }).on('blur', function () {
    setTimeout(() => {
      $('#nameHelp').hide();
    }, 500);
  }).on('focus', function () {
    const name = $('#name').val();
    const validName = /^[A-Za-z\s]+$/;

    if (!validName.test(name)) {
      $('#nameHelp').show();
    }
  });

  // Hint Email
  $('#inputEmail').on('input', function () {
    const email = $(this).val();
    const validEmail = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;

    if (!validEmail.test(email)) {
      $('#emailHelp').show();
    } else {
      $('#emailHelp').hide();
    }
  }).on('blur', function () {
    setTimeout(() => {
      $('#emailHelp').hide();
    }, 500);
  }).on('focus', function () {
    const email = $('#inputEmail').val();
    const validEmail = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;

    if (!validEmail.test(email)) {
      $('#emailHelp').show();
    }
  });


  // Hint Phone
  $('#inputPhone').on('input', function () {
    const phone = $(this).val();
    const startWith08 = /^08/;
    const lengthValid = phone.length >= 11 && phone.length <= 14;

    // Periksa apakah nomor dimulai dengan "08" dan panjang valid
    if (!startWith08.test(phone)) {
      $('#phoneHelpStart').show();
    } else {
      $('#phoneHelpStart').hide();
    }

    if (!lengthValid) {
      $('#phoneHelpLength').show();
    } else {
      $('#phoneHelpLength').hide();
    }
  }).on('blur', function () {

    setTimeout(() => {
      $('#phoneHelpStart').hide();
      $('#phoneHelpLength').hide();
    }, 500);
  }).on('focus', function () {

    const phone = $(this).val();
    const startWith08 = /^08/;
    const lengthValid = phone.length >= 11 && phone.length <= 14;


    if (!startWith08.test(phone)) {
      $('#phoneHelpStart').show();
    } else {
      $('#phoneHelpStart').hide();
    }

    if (!lengthValid) {
      $('#phoneHelpLength').show();
    } else {
      $('#phoneHelpLength').hide();
    }
  });

  $(".toggle-password").on("click", function () {
    const input = $($(this).attr("toggle")); // Input terkait
    const icon = $(this); // Ikon itu sendiri

    // Toggle tipe input antara password dan text
    if (input.attr("type") === "password") {
      input.attr("type", "text");
      icon.removeClass("fa-eye-slash").addClass("fa-eye");
    } else {
      input.attr("type", "password");
      icon.removeClass("fa-eye").addClass("fa-eye-slash");
    }
  });

  $('.alert').each(function () {
    startProgressBarAndRemoveAlert($(this));
  });

  $('#profileDropdown').hover(
    function () {
      $('.profileDropdown').stop(true, true).fadeIn(200); // Tampilkan dropdown saat hover
      adjustDropdownPositionProfile(); // Sesuaikan posisi dropdown jika diperlukan
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

  function adjustDropdownPositionProfile() {
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


  $('#checkoutButton').on('click', function (event) {
    event.preventDefault(); // Prevent the default form submission

    $.ajax({
      url: '/create-transaction',
      type: 'POST',
      data: $('#deliveryOptionForm').serialize(), // Serialize form data
      success: function (response) {
        if (response.snap_token) {
          snap.pay(response.snap_token, {
            onSuccess: function (result) {
              window.location.href = "/pesanan";
            },
            onPending: function (result) {
              window.location.href = "/pesanan";
            },
            onError: function (result) {
            },
            onClose: function () {
              window.location.href = "/pesanan";
            }
          });
        } else {
          alert('Failed to get payment token.');
        }
      },
      error: function (xhr, status, error) {
        console.error('AJAX Error:', error);
        alert('An error occurred while creating the transaction.');
      }
    });
  });

  // Initialize the map
  const map = L.map('map').setView([-6.876916, 109.047849], 10);

  // Load the HD tile layer from Thunderforest
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  let marker;

  // Store address coordinates (change to your actual store location)
  const storeLat = -6.876916;  // Replace with your store latitude
  const storeLng = 109.047849; // Replace with your store longitude

  
  // Add a marker for the store location with the custom icon
  const storeMarker = L.marker([storeLat, storeLng]).addTo(map)
    .bindPopup('Lokasi Toko Kami')
    .openPopup();

  // Function to get current location
  function getLocation() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(showPosition, showError);
    } else {
      alert('Geolocation is not supported by this browser.');
    }
  }

  // Function to handle successful geolocation
  function showPosition(position) {
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;

    // Center map to current location
    map.setView([lat, lng], 17);

    // Add or update marker on map
    if (marker) {
      marker.setLatLng([lat, lng]);
    } else {
      marker = L.marker([lat, lng], { draggable: true }).addTo(map)
        .bindPopup('Lokasi Anda Sekarang')
        .openPopup();
    }

    // Update coordinates in hidden inputs
    updateCoordinates(lat, lng);

    // Update address fields based on location
    marker.on('dragend', function (e) {
      const { lat, lng } = e.target.getLatLng();
      updateCoordinates(lat, lng);
    });
  }

  // Function to handle geolocation errors
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

  // Function to update coordinates in the hidden fields
  function updateCoordinates(lat, lng) {
    document.getElementById('latitude').value = lat;
    document.getElementById('longitude').value = lng;

    // Check distance from default location and update the button state
    checkDistance(lat, lng);

    // Update address fields based on coordinates
    updateAddressFields(lat, lng);
  }

  // Function to update address fields based on coordinates
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

  // Function to check the distance from the default location
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

        if (distanceInKm > 60) {
          saveButton.disabled = true;
          saveButton.classList.add('btn-secondary'); // Optional: Change button style to indicate it's disabled
          alert('Jarak dari lokasi toko lebih dari 60 km. Alamat tidak dapat disimpan.');
        } else {
          saveButton.disabled = false;
          saveButton.classList.remove('btn-secondary'); // Optional: Restore original button style
        }
      })
      .catch(error => console.error('Error:', error));
  }

  // Map click event to set marker
  map.on('click', function (e) {
    const { lat, lng } = e.latlng;

    if (marker) {
      marker.setLatLng([lat, lng]);
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

  // Event listener to initialize map when modal is shown
  document.getElementById('addAddressModal').addEventListener('shown.bs.modal', function () {
    map.invalidateSize();
    getLocation();
  });


  // Event listener to initialize map when modal is shown
  document.getElementById('addAddressModal').addEventListener('shown.bs.modal', function () {
    map.invalidateSize();
    getLocation();
  });

  // Mendapatkan tanggal saat ini dan menambahkan 3 hari
  const today = new Date();
  today.setDate(today.getDate() + 3); // Tambahkan 3 hari dari hari ini
  const dd = String(today.getDate()).padStart(2, '0');
  const mm = String(today.getMonth() + 1).padStart(2, '0');
  const yyyy = today.getFullYear();
  const minDate = `${yyyy}-${mm}-${dd}`;

  // Ambil elemen input
  const $deliveryDateInput = $('#delivery-date');
  const $deliveryTimeInput = $('#delivery-time');
  const $checkoutButton = $('#checkoutButton');

  // Set atribut minimal tanggal pengiriman
  $deliveryDateInput.attr('min', minDate);

  // Nonaktifkan input waktu dan tombol checkout di awal
  $deliveryTimeInput.prop('disabled', true);
  $checkoutButton.prop('disabled', true);

  // Validasi tanggal saat tanggal dipilih
  $deliveryDateInput.on('blur change', function () {
    const selectedDate = new Date($deliveryDateInput.val());
    const currentDate = new Date();
    currentDate.setDate(currentDate.getDate() + 2); // Batas minimal 3 hari ke depan

    if ($deliveryDateInput.val()) {
      if (selectedDate < currentDate) {
        alert("Tanggal pengiriman harus minimal 3 hari dari hari ini.");
        $deliveryDateInput.val(''); // Reset input tanggal
        $deliveryTimeInput.prop('disabled', true); // Disable kembali waktu
      } else {
        // Jika tanggal valid, aktifkan input waktu
        $deliveryTimeInput.prop('disabled', false);
        $deliveryTimeInput.val('06:00');
      }
    }
    checkDateAndTime();
  });

  // Validasi waktu pengiriman
  $deliveryTimeInput.on('blur change', function () {

    checkDateAndTime();
  });

  // Fungsi untuk memeriksa apakah tanggal dan waktu valid
  function checkDateAndTime() {
    const selectedDate = $deliveryDateInput.val();
    const selectedTime = $deliveryTimeInput.val();
    const [hours, minutes] = selectedTime.split(':').map(Number);


    const validTime = (hours >= 6 && hours < 20) || (hours === 20 && minutes === 0);
    if (selectedDate && selectedTime && validTime) {
      // Jika keduanya valid, aktifkan tombol checkout
      $checkoutButton.prop('disabled', false);
    } else {
      // Jika salah satu kosong atau waktu tidak valid, nonaktifkan tombol checkout
      $checkoutButton.prop('disabled', true);
      if (selectedTime && !validTime) {
        alert("Waktu pengiriman harus antara 06:00 dan 20:00.");
        $deliveryTimeInput.val('');

      }
    }
  }

});




