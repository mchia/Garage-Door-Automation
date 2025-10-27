SELECT
    lb.session_id,
    u.username,
    lb.login_date,
    lb.login_time,
    lb.ip_address,
    ip.city,
    ip.region,
    ip.country,
    lb.browser || ' ' || lb.browser_version as browser,
    lb.os || ' ' || lb.os_version as os,
    CASE
        WHEN UPPER(lb.device) = 'K' then 'Android'
        ELSE lb.device
    END AS device
FROM
    logbook lb
    INNER JOIN users u ON lb.user_id = u.id
    INNER JOIN ip_logs ip ON lb.ip_address = ip.ip_address
ORDER BY
    lb.login_date DESC,
    lb.login_time DESC