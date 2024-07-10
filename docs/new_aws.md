# AWS hosts

1. Create a new AWS instance
  - Use Amazon Linux
  - m7a.xlarge: 4 cores, enough memory
  - Network Settings: "Create Security Group", "Allow SSH traffic from: Anywhere"
  - Select more than 64GB of EBS
2. In the instance page, get the "Public IPv4 DNS" hostname
3. `ssh ec2-user@<hostname>`
4. Copy `devenv/bin/setup_system_user` to the server, sudo python3 it
5. Copy `devenv/bin/fixmydev` to the server, python3 it (maybe with -i)
6. Exit. I can now ssh into the host as njormrod
