<?php
// Set email to receive the alert
//$to = "  ";  // Replace with your email address
//$subject = "Honeypot Alert: Potential Intruder";


//<?php
$to = "  ";
$subject = "Test Email";
$message = "This is a test email.";
$headers = "From: test@example.com\r\n";

if (mail($to, $subject, $message, $headers)) {
    echo "Email sent successfully.";
} else {
    echo "Failed to send email.";
}
?>
// Get the visitor's IP address
//$ip = $_SERVER['REMOTE_ADDR'];

// Geolocation API URL (IP Geolocation service)
//$geolocation_url = "http://ip-api.com/json/{$ip}?fields=country,region,city,isp,org,query,lat,lon";

// Fetch geolocation data
//$geo_data = file_get_contents($geolocation_url);
//$geo = json_decode($geo_data, true);

// Get the current date and time
//$date = date("Y-m-d H:i:s");

// Collect details about the request
//$referrer = isset($_SERVER['HTTP_REFERER']) ? $_SERVER['HTTP_REFERER'] : "No Referrer";
//$user_agent = $_SERVER['HTTP_USER_AGENT'];

// Prepare the message body
//$message = "ALERT - Honeypot Triggered!\n\n";
//$message .= "Date and Time: {$date}\n";
//$message .= "IP Address: {$ip}\n";
//$message .= "Location: {$geo['city']}, {$geo['region']}, {$geo['country']}\n";
//$message .= "ISP: {$geo['isp']}\n";
//$message .= "Organization: {$geo['org']}\n";
//$message .= "Latitude/Longitude: {$geo['lat']}, {$geo['lon']}\n";
//$message .= "User Agent: {$user_agent}\n";
//$message .= "Referrer: {$referrer}\n";

// Send an email
//$headers = "From: honeypot-alert@example.com\r\n";
//$headers .= "Reply-To: no-reply@example.com\r\n";
//$headers .= "Content-Type: text/plain; charset=UTF-8\r\n";

// mail($to, $subject, $message, $headers);

//if (mail($to, $subject, $message, $headers)) {
//    echo "Email sent successfully.";
//} else {
//   echo "Failed to send email.";
//}

// Optionally, you can also log this to a file
//$logfile = 'honeypot_log.txt'; // Log file path
//$log_message = "Date: {$date}, IP: {$ip}, Location: {$geo['city']}, {$geo['region']}, {$geo['country']}, User Agent: {$user_agent}\n";
//file_put_contents($logfile, $log_message, FILE_APPEND);

//exit();
//?>