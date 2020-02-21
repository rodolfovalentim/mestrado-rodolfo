# Nuvem 1

| Nó         | IP           | Username | Password |
| ---------- | ------------ | -------- | -------- |
| Controller | 192.168.0.40 | stack    | stack    |
| Compute    | 192.168.0.41 | stack    | stack    |

# Nuvem 2 (all in one)

| Nó         | IP           | Username | Password |
| ---------- | ------------ | -------- | -------- |
| All in one | 192.168.0.50 | stack    | stack    |

# Scripts utilizados para instalação do OpenStack em CentOS

HOSTNAME=controller
INTERFACE_MGMT=em1
IP_MGMT=10.62.0.2
NETMASK_MGMT=255.255.254.0
GATEWAY_MGMT=10.62.255.254

INTERFACE_PROVIDER=em2

# Adicionar o usuario stack ao sudoers

usermod -aG wheel stack

# Feche a conexão ssh e abra novament

sudo su

# atualize os pacotes

yum update -y
yum install net-tools nano -y

# Configure a interface eno1 com IP fixo

ifconfig $INTERFACE_MGMT $IP_MGMT netmask $NETMASK_MGMT
echo "nameserver 8.8.8.8" > /etc/resolv.conf
nmcli con mod $INTERFACE_MGMT connection.autoconnect yes
nmcli con down $INTERFACE_MGMT; nmcli con up $INTERFACE_MGMT

ip route add default via $GATEWAY_MGMT dev $INTERFACE_MGMT

# Configure a interface eno2

ifconfig $INTERFACE_PROVIDER up
nmcli con mod $INTERFACE_PROVIDER connection.autoconnect yes
nmcli con mod $INTERFACE_PROVIDER ipv4.method disabled

# Configure hosts

echo "$IP_MGMT  $HOSTNAME" >> /etc/hosts

# Instale dependencias

yum install python-devel libffi-devel gcc openssl-devel libselinux-python python-virtualenv git -y

# desabilite SELinux:

/usr/sbin/setenforce 0

# Edite /etc/sysconfig/selinux e configure da seguinte forma:

SELINUX=disabled
SELINUXTYPE=targeted

# Desabilite firewalld

systemctl disable firewalld
systemctl stop firewalld
systemctl status firewalld

# Instalar docker

curl -sSL https://get.docker.io | bash
groupadd docker
usermod -aG docker stack
newgrp docker

# Ative e começe o serviço

systemctl enable docker
systemctl start docker
systemctl status docker

# Saia do su

exit

# Crie um ambiente virtual python para instalar utilizando docker. Essa é uma boa prática para isolar as instalações

virtualenv ~/installenv
source ~/installenv/bin/activate
pip install ansible==2.7.0
pip install requests==2.22.0
pip install docker.py==2.0.0
pip install tox

cd ~
git clone https://github.com/openstack/kolla -b stable/rocky
cd kolla
pip install .

cd ~
git clone https://github.com/openstack/kolla-ansible -b stable/rocky
cd kolla-ansible
pip install .

sudo mkdir -p /etc/kolla
sudo chown $USER:$USER /etc/kolla

cd ~
cp -r kolla-ansible/etc/kolla/_ /etc/kolla
cp kolla-ansible/ansible/inventory/_ .

# Crie chave ssh e copie para os nós

ssh-keygen
ssh-copy-id stack@controller

# For development, run:

cd ~/kolla-ansible/tools
./generate_passwords.py

# Edit the /etc/kolla/passwords.yml. Change the keystone_admin_password to a desired value.

keystone_admin_password: stack

# Crie a pasta e o arquivo

sudo mkdir /etc/ansible
sudo nano /etc/ansible/hosts

# Cole

[controller]
controller

[compute]
compute

# Caso tenha-se algum problema com as imagens, recrie as imagens

cd ~/kolla
tox -e genconfig
.tox/genconfig/bin/kolla-build -b centos

# Deploy as imagens!

cd kolla-ansible/tools
./kolla-ansible -i ~/all-in-one bootstrap-servers
./kolla-ansible -i ~/all-in-one prechecks
./kolla-ansible -i ~/all-in-one deploy

# Configure OVS

sudo yum install @'Development Tools' rpm-build yum-utils subscription-manager -y
sudo yum -y remove kernel-devel*
sudo yum -y install kernel-devel*

export kernel_headers=`ls -hd /usr/src/kernels/3*`
sudo ln -s ${kernel_headers}/include/generated/uapi/linux/version.h ${kernel_headers}/include/linux/version.h

git clone https://github.com/openvswitch/ovs.git
git checkout tags/v2.11.0

sed -e 's/@VERSION@/0.0.1/' rhel/openvswitch-fedora.spec.in \

> /tmp/ovs.spec

sudo yum-builddep /tmp/ovs.spec
make rpm-fedora
