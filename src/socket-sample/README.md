## Thư viện socket của python 3
### Tìm hiểu một số phương thức:

```text
bind(ip_address, port) : Dùng để lắng nghe đến địa chỉ ip và cổng
listen(2) : Cho socket đang lắng nghe tới tối đa 2 kết nối
accept() : Khi một client gõ cửa, server chấp nhận kết nối và 1 socket mới được tạo ra. Client và server bây giờ đã có thể truyền và nhận dữ liệu với nhau
connect(ip_address) : Thiết lập một kết nối từ client đến server.
recv(bufsize, flag) : Phương thức này được sử dụng để nhận dữ liệu qua giao thức TCP.
recvfrom(bufsize, flag) : Nhận dữ liệu qua UDP
send(byte, flag) : Phương thức này để gửi dữ liệu qua TCP
sendto(bytes, flag) : Gửi dữ liệu qua UDP
sendall(bytes(msg, "utf8")) : Gửi dữ liệu thông qua giao thức TCP
close() : Đóng một kết nối 
```


### Kiểu thiết lập kết nối:
 - AF_INET: Ipv4
 - AF_INET6: Ipv6
 - AF_UNIX
### Socket Type:
 - SOCK_STREAM: TCP
 - SOCK_DGRAM: UDP


### Flow
![img_flow](images/sockets-tcp-flow.webp)

### Demo
![img](images/test.png)
