"""Role testing files using testinfra."""


def test_directory_running(host):
    with host.sudo():
        command = r"""set -o pipefail && echo '123ADMin'| \
        kinit admin > /dev/null && \
        ipactl status | \
        grep -c 'Directory Service: RUNNING'"""
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_krb5kdc_running(host):
    with host.sudo():
        command = r"""set -o pipefail && echo '123ADMin'| \
        kinit admin > /dev/null && \
        ipactl status | \
        grep -c 'krb5kdc Service: RUNNING'"""
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_kadmin_running(host):
    command = r"""set -o pipefail && echo '123ADMin'| \
    kinit admin > /dev/null && \
    ipactl status | \
    grep -c 'kadmin Service: RUNNING'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_dns_running(host):
    command = r"""set -o pipefail && echo '123ADMin'| \
    kinit admin > /dev/null && \
    ipactl status | \
    grep -c 'named Service: RUNNING'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_https_running(host):
    command = r"""set -o pipefail && echo '123ADMin'| \
    kinit admin > /dev/null && \
    ipactl status | \
    grep -c 'httpd Service: RUNNING'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_custodia_running(host):
    command = r"""set -o pipefail && echo '123ADMin'| \
    kinit admin > /dev/null && \
    ipactl status | \
    grep -c 'ipa-custodia Service: RUNNING'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_pki_running(host):
    command = r"""set -o pipefail && echo '123ADMin'| \
    kinit admin > /dev/null && \
    ipactl status | \
    grep -c 'pki-tomcatd Service: RUNNING'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_otp_running(host):
    command = r"""set -o pipefail && echo '123ADMin'| \
    kinit admin > /dev/null && \
    ipactl status | \
    grep -c 'ipa-otpd Service: RUNNING'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_dnskey_running(host):
    command = r"""set -o pipefail && echo '123ADMin'| \
    kinit admin > /dev/null && \
    ipactl status | \
    grep -c 'ipa-dnskeysyncd Service: RUNNING'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_ipa_ldap_opened_in_firewall(host):
    command = r"""set -o pipefail && \
    firewall-cmd --list-services --zone=internal | \
    grep -c 'freeipa-ldap'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_ipa_ldaps_opened_in_firewall(host):
    command = r"""set -o pipefail && \
    firewall-cmd --list-services --zone=internal | \
    grep -c 'freeipa-ldaps'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_ipa_https_opened_in_firewall(host):
    command = r"""set -o pipefail && \
    firewall-cmd --list-services --zone=internal | \
    grep -c 'https'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_ipa_dns_opened_in_firewall(host):
    command = r"""set -o pipefail && \
    firewall-cmd --list-services --zone=internal | \
    grep -c 'dns'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_user_exists(host):
    command = r"""set -o pipefail && echo '123ADMin'| \
    kinit admin > /dev/null && \
    ipa user-find admin | \
    grep -c 'Last name: Administrator'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_acme_enabled(host):
    command = r"""set -o pipefail && echo '123ADMin'| \
    kinit admin > /dev/null && \
    ipa-acme-manage status | \
    grep -c 'ACME is enabled'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout


def test_https_opened_in_firewall(host):
    command = r"""set -o pipefail && \
    firewall-cmd --list-services --zone=internal | \
    grep -c 'https'"""
    with host.sudo():
        cmd = host.run(command)
    assert '1' in cmd.stdout
