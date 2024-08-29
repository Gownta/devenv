# Ansible

pip3 install ansible

`go -e username=njormrod`
`ansible-playbook -i <hostname>, -e ansible_user=ec2-user playbook.yaml`


# Core concepts

The "Control Node" runs ansible, and it configures the "Managed Nodes".
The list of nodes to manage is the "Inventory", defined in inventory.ini.


# References

[Playbook docs](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_intro.html)
[Existing collections](https://docs.ansible.com/ansible/latest/collections/index.html)
[Esp ansible.builtin](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/index.html)
[Complex control flow](https://docs.ansible.com/ansible/latest/playbook_guide/complex_data_manipulation.htm)
[Playbook reuse](https://docs.ansible.com/ansible-core/2.15/playbook_guide/playbooks_reuse.html#playbooks-reuse)
