document.addEventListener("DOMContentLoaded", function () {
    function convertPersianToEnglish(str) {
      const persianDigits = "۰۱۲۳۴۵۶۷۸۹";
      const englishDigits = "0123456789";
      return str.replace(/[۰-۹]/g, d => englishDigits[persianDigits.indexOf(d)]);
    }
  
    function addCommas(str) {
      str = convertPersianToEnglish(str.replace(/,/g, ""));
      let parts = str.split(".");
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      return parts.join(".");
    }
  
    ["id_price_level_1", "id_price_level_2", "id_volume_value"].forEach(id => {
      const input = document.getElementById(id);
      if (input) {
        input.addEventListener("input", e => {
          const value = addCommas(e.target.value);
          e.target.value = value;
        });
      }
    });
  });