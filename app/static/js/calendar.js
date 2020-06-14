var Cal = function(divId) {

  //Store div id
  this.divId = divId;

  // Days of week, starting on Sunday
  this.DaysOfWeek = [
    'Mon',
    'Tue',
    'Wed',
    'Thu',
    'Fri',
    'Sat',
    'Sun',
  ];

  // Months, stating on January
  this.Months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December' ];

  // Set the current month, year
  var d = new Date();

  this.currMonth = d.getMonth();
  this.currYear = d.getFullYear();
  this.currDay = d.getDate();

};

// Goes to next month
Cal.prototype.nextMonth = function() {
  if ( this.currMonth == 11 ) {
    this.currMonth = 0;
    this.currYear = this.currYear + 1;
  }
  else {
    this.currMonth = this.currMonth + 1;
  }
  this.showcurr();
};

// Goes to previous month
Cal.prototype.previousMonth = function() {
  if ( this.currMonth == 0 ) {
    this.currMonth = 11;
    this.currYear = this.currYear - 1;
  }
  else {
    this.currMonth = this.currMonth - 1;
  }
  this.showcurr();
};

// Show current month
Cal.prototype.showcurr = function() {

  // Define variable to access this in AJAX call
  var self = this;

  // Get list of days for given month with information entry (sensor data, plot, annotations...)
  $(function(){$.ajax( {
    type: "POST",
    url: "_get_info_json/",
    contentType: "application/json",
    data: JSON.stringify({year: self.currYear, month: self.currMonth}),
    dataType: "json",
    success: function(response) {
        info = response.notes;
        self.showMonth(self.currYear, self.currMonth, info);
        },
    })});

};

// Show month (year, month)
Cal.prototype.showMonth = function(y, m, info) {

  var d = new Date()
  // First day of the week in the selected month
  , firstDayOfMonth = new Date(y, m, 1).getDay()
  // Last day of the selected month
  , lastDateOfMonth =  new Date(y, m+1, 0).getDate()
  // Last day of the previous month
  , lastDayOfLastMonth = m == 0 ? new Date(y-1, 11, 0).getDate() : new Date(y, m, 0).getDate();

  var html = '<table class="cal">';

  // Write selected month and year
  html += '<thead class="cal"><tr>';
  html += '<td class="cal" colspan="7">' + this.Months[m] + ' ' + y + '</td>';
  html += '</tr></thead>';

  // Write the header of the days of the week
  html += '<tr class="days">';
  for(var i=0; i < this.DaysOfWeek.length;i++) {
    html += '<td class="cal">' + this.DaysOfWeek[i] + '</td>';
  }
  html += '</tr>';

  // Write the days
  var i=1;
  do {

    var dow = new Date(y, m, i).getDay();

    // If Sunday, start new row
    if ( dow == 0 ) {
      html += '<tr>';
    }
    // If not Sunday but first day of the month
    // it will write the last days from the previous month
    else if ( i == 1 ) {
      html += '<tr>';
      var k = lastDayOfLastMonth - firstDayOfMonth+1;
      for(var j=0; j < firstDayOfMonth; j++) {
        html += '<td class="cal not-current">' + k + '</td>';
        k++;
      }
    };

    // Write the current day in the loop
    var chk = new Date();
    var chkY = chk.getFullYear();
    var chkM = chk.getMonth();
    var name_attr = `year="${y}" month="${m}" day="${i}"`;

    // Background colour for days with info entry
    var bg = "";
    if (info.indexOf(i) > -1) {
        bg = " info";
    }

    if (chkY == this.currYear && chkM == this.currMonth && i == this.currDay) {
      html += '<td class="cal today' + bg + '"><button id="btnDay" type="button" ' + name_attr + '>' + i + '</button></td>';
    } else {
      html += '<td class="cal normal' + bg + '"><button id="btnDay" type="button" ' + name_attr + '>' + i + '</button></td>';
    };
    // If Sunday, closes the row
    if ( dow == 6 ) {
      html += '</tr>';
    }
    // If not Sunday, but last day of the selected month
    // it will write the next few days from the next month
    else if ( i == lastDateOfMonth ) {
      var k=1;
      for(dow; dow < 6; dow++) {
        html += '<td class="cal not-current">' + k + '</td>';
        k++;
      }
    }

    i++;
  }while(i <= lastDateOfMonth);

  // Closes table
  html += '</table>';

  // Write HTML to the div
  document.getElementById(this.divId).innerHTML = html;
};


// On Load of the window
window.onload = function() {

  // Start calendar
  var c = new Cal("divCal");
  c.showcurr();

  // Bind next and previous button clicks
  getId('btnNext').onclick = function() {


    c.nextMonth();
  };
  getId('btnPrev').onclick = function() {
    c.previousMonth();
  };
}

// Get element by id
function getId(id) {
  return document.getElementById(id);
}

// Get data from Flask when clicking on a day in the calendar
$(document).on("click", "#btnDay", function(){

    var d = $(this).attr("day");

     $(function(){$.ajax( {
            type: "POST",
            url: "_get_post_json/",
            contentType: "application/json",
            data: JSON.stringify({day: d}),
            dataType: "json",
            success: function(response) {
                $("#result").html("<p>" + response.message + "</p>");
                },
            })});

  });
