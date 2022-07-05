:title: SELinux and Kubernetes: Writing Custom Policies
:slug: selinux-for-k8s
:sortorder: 20
:date: 2022-07-05

If you run containerized applications on hosts with SELinux enforcing, whether
with Kubernetes or just the bare container runtime, there may be barriers to
the application functioning correctly. While you could simply run ``setenforce
0`` and be done, wouldn't it instead be fun to write some SELinux policy for
your app? This post will show the process of debugging and building policies
for a containerized logging application running on an SELinux-enforcing host
and explain some of the tools available to help.

Prerequisites
=============

We can use CentOS 8 to learn how to debug SELinux with kubernetes.

Ensure SELinux is set to ``Enforcing``:

.. code-block:: console

   $ sudo getenforce
   Enforcing

Install utilities for querying SELinux status and developing policy:

.. code-block:: console

   $ sudo dnf install setools-console selinux-policy-devel

Setup
=====

We will use kubeadm as the Kubernetes deployer and `Docker
<https://docs.docker.com/engine/install/centos/>`_ as the container runtime.
Similar issues can be observed in other container runtimes, but may be easier to
resolve without custom policies. Docker additionally needs to have SELinux
enabled in its own configuration:

.. code-block:: console

   $ sudo mkdir -p /etc/docker
   $ sudo echo '{"selinux-enabled": true}' > /etc/docker/daemon.json
   $ sudo systemctl restart docker

Kubeadm does not officially support SELinux, and in fact the installation
instructions explicitly have you turn it off. However, `it is not
impossible <https://github.com/kubernetes/kubeadm/issues/1654>`_. Before
installing kubeadm, prepare the directories it needs with the right labels:

.. code-block:: console

   $ sudo mkdir -p /var/lib/etcd
   $ sudo mkdir -p /etc/kubernetes/pki
   $ sudo chcon -R -t svirt_sandbox_file_t /var/lib/etcd
   $ sudo chcon -R -t svirt_sandbox_file_t /etc/kubernetes

Then you can proceed to `install
kubeadm <https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm>`_
following the "Red Hat-based distributions" tab, but do NOT run ``sudo
setenforce 0`` and do NOT modify ``/etc/selinux/config``. `Create a
cluster <https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm>`_
(a single-node cluster is fine). Kubernetes 1.24 no longer supports running on
Docker directly, so for the sake of this example, install Kubernetes 1.23.

.. code-block:: console

   $ sudo dnf install -y kubelet-1.23.8 kubeadm-1.23.8 kubectl-1.23.8 --disableexcludes=kubernetes

The `Banzai logging operator
<https://banzaicloud.com/docs/one-eye/logging-operator>`_ needs to access log
files on the host, which makes it an easy victim for SELinux to stop in its
tracks. Deploy it with helm:

.. code-block:: console

   $ helm repo add banzaicloud-stable https://kubernetes-charts.banzaicloud.com
   "banzaicloud-stable" has been added to your repositories
   $ helm repo update
   Hang tight while we grab the latest from your chart repositories...
   ...Successfully got an update from the "banzaicloud-stable" chart repository
   Update Complete. ⎈Happy Helming!⎈
   $ helm upgrade --install --wait --create-namespace --namespace logging logging-operator banzaicloud-stable/logging-operator
   Release "logging-operator" does not exist. Installing it now.
   ...
   $ cat logging.yaml
   apiVersion: logging.banzaicloud.io/v1beta1
   kind: Logging
   metadata:
     name: logging
   spec:
     fluentbit: {}
     fluentd:
       disablePvc: true
     controlNamespace: logging
   $ kubectl apply -f logging.yaml
   logging.logging.banzaicloud.io/logging created

Symptoms
========

Looking at the logs from the fluentbit pod, we can tell it's not working:

.. code-block:: console

   $ kubectl -n logging logs -l app.kubernetes.io/name=fluentbit
   [2022/06/27 18:10:55] [error] [input:tail:tail.0] read error, check permissions: /var/log/containers/*.log
   [2022/06/27 18:10:55] [ warn] [input:tail:tail.0] error scanning path: /var/log/containers/*.log
   [2022/06/27 18:11:00] [error] [input:tail:tail.0] read error, check permissions: /var/log/containers/*.log
   [2022/06/27 18:11:00] [ warn] [input:tail:tail.0] error scanning path: /var/log/containers/*.log

How do we know it's an SELinux problem? You may be used to dealing with
standard Linux filesystem permissions, where the fix is just to ``chown`` or
``chmod`` a file to allow the user use it, or to modify the user (``usermod -a
-G``) or use a different user (``sudo``/``su``). Those solutions won't work in this
case. We can note that the container is already running as root:

.. code-block:: console

   $ container=$(docker ps | awk '/fluent-bit/{print $1}')
   $ docker inspect $container | jq .[0].Config.User
   "0"
   $ pid=$(docker inspect $container | jq .[0].State.Pid)
   $ ps -o user $pid
   USER
   root

So regular filesystem permissions shouldn't be a barrier here. Some other kind
of access control system is at play, and we can guess that it's SELinux, and
verify by either temporarily turning off SELinux:

.. code-block:: console

   $ sudo setenforce 0
   $ kubectl -n logging rollout restart daemonset logging-fluentbit
   daemonset.apps/logging-fluentbit restarted
   $ kubectl -n logging logs -l app.kubernetes.io/name=fluentbit
   [2022/06/27 18:14:21] [ info] [input:tail:tail.0] inotify_fs_add(): inode=234898005 watch_fd=13 name=/var/log/containers/logging-fluentd-0_default_config-reloader-7d87aa862742e1388ed9a79f7c4d80b1a6146f572ec5cc1db6b61c4fed9e897b.log
   [2022/06/27 18:14:21] [ info] [input:tail:tail.0] inotify_fs_add(): inode=318769123 watch_fd=14 name=/var/log/containers/logging-fluentd-0_default_fluentd-b1247e84bf77408773a2ad51cfd8390337374c35537507ab1ba87f02e29f16cb.log
   [2022/06/27 18:14:21] [ info] [input:tail:tail.0] inotify_fs_add(): inode=192945986 watch_fd=15 name=/var/log/containers/logging-fluentd-configcheck-c3054702_default_fluentd-f2249eeffde6de8792e4c21ae78f1ddbc43a45d0fc332f676eac3567c0851c7e.log
   [2022/06/27 18:14:21] [ info] [input:tail:tail.0] inotify_fs_add(): inode=180371584 watch_fd=16 name=/var/log/containers/logging-rancher-logging-568b59f59b-mztq8_default_rancher-logging-bcbf0feb1889c7d8d9e523aaa8e9d2308d3750efc14b44c75751147847347947.log

or modifying the pod to run as a superprivileged container:

.. code-block:: console

   $ kubectl -n logging patch daemonset logging-fluentbit -p '{"spec": {"template": {"spec": {"containers":[{"name": "fluent-bit", "securityContext": {"seLinuxOptions": {"type": "spc_t"}}}]}}}}'
   daemonset.apps/logging-fluentbit patched
   $ kubectl -n logging logs -l app.kubernetes.io/name=fluentbit
   [2021/03/28 16:39:19] [ info] [input:tail:tail.0] inotify_fs_add(): inode=2108899 watch_fd=23 name=/var/log/containers/logging-fluentd-0_default_config-reloader-2a8ef4bdc8cc3442d96e879d82b29f9c04c064996c9d0ab378264aec6774ab96.log
   [2021/03/28 16:39:19] [ info] [input:tail:tail.0] inotify_fs_add(): inode=1603298 watch_fd=24 name=/var/log/containers/logging-fluentd-0_default_config-reloader-d75335a76cab2fe54b58c2a701c3cf8c1058bcfea809a46e167e5d11cc3274b4.log
   [2021/03/28 16:39:19] [ info] [input:tail:tail.0] inotify_fs_add(): inode=1603173 watch_fd=25 name=/var/log/containers/logging-fluentd-0_default_fluentd-770f84f8c0f0cbf209bff21958f2b4e2439101055b61ad08faa2b0545bc8e9f1.log
   [2021/03/28 16:39:19] [ info] [input:tail:tail.0] inotify_fs_add(): inode=2108856 watch_fd=26 name=/var/log/containers/logging-fluentd-0_default_fluentd-cfc6587c5ead152fb2ed87114e86f7f0625ff41b760659c8c4ce7037b008ebf9.log

The app is running as expected, but these aren't permanent solutions, we've
only confirmed the problem. Turn enforcing back on now:

.. code-block:: console

   $ sudo setenforce 1

or remove the security context from the pod:

.. code-block:: console

   $ kubectl patch daemonset logging-fluentbit --type=json -p '[{"op": "remove", "path": "/spec/template/spec/containers/0/securityContext/seLinuxOptions"}]'

Diagnosis
=========

We can take a closer look at the application manifest, and notice what
filesystems it's mounting:

.. code-block:: console

   $ kubectl -n logging describe daemonset logging-fluentbit | grep -A 8 Volumes
     Volumes:
      varlibcontainers:
       Type:          HostPath (bare host directory volume)
       Path:          /var/lib/docker/containers
       HostPathType:
      varlogs:
       Type:          HostPath (bare host directory volume)
       Path:          /var/log
       HostPathType:

/var/log was the volume it was emitting permission errors on, so that makes
sense. On the host system, we can look more closely at this directory:

.. code-block:: console

   $ sudo ls -lZd /var/log/containers
   drwxr-xr-x. 2 root root system_u:object_r:container_log_t:s0 4096 Jun 27 19:41 /var/log/containers
   $ sudo ls -lZ /var/log/containers
   lrwxrwxrwx. 1 root root system_u:object_r:container_log_t:s0 135 Jun 27 19:40 calico-kube-controllers-7f87b64bd9-n2tls_calico-system_calico-kube-controllers-8ab96358bc771647242dbd04af0f2e0c27134c7a3a9d4597b5a818836c6df279.log -> /var/log/pods/calico-system_calico-kube-controllers-7f87b64bd9-n2tls_23a03fc1-11cc-44c7-80a1-f1c9c370bee8/calico-kube-controllers/0.log
   lrwxrwxrwx. 1 root root system_u:object_r:container_log_t:s0 100 Jun 27 19:40 calico-node-l4tjb_calico-system_install-cni-b29f2b937973886b27d24e7e243dd82e59d2b2bf812b1ec34a13cacd79f8b90e.log -> /var/log/pods/calico-system_calico-node-l4tjb_0597fd03-1d8b-4fb6-a786-c330da8c18d9/install-cni/0.log
   lrwxrwxrwx. 1 root root system_u:object_r:container_log_t:s0 101 Jun 27 19:40 coredns-558bd4d5db-6z9gm_kube-system_coredns-9c1cd7d657dd53f60921043927abeb02179893a4231296be104fa4e3c07236ab.log -> /var/log/pods/kube-system_coredns-558bd4d5db-6z9gm_c43d3862-4c0f-4239-85bd-d136724cee2f/coredns/0.log
   lrwxrwxrwx. 1 root root system_u:object_r:container_log_t:s0  79 Jun 27 19:39 etcd-demo_kube-system_etcd-f769696c9e621846d0ae63f12f3f4207c3a390968032a43ec5f881c0223c45a3.log -> /var/log/pods/kube-system_etcd-demo_6a45c8016b879de1f0da7753790d707a/etcd/0.log
   lrwxrwxrwx. 1 root root system_u:object_r:container_log_t:s0  99 Jun 27 19:39 kube-apiserver-demo_kube-system_kube-apiserver-79b1192098264baf2580c4709cf263facad0ff747de488348274b580cf58f52b.log -> /var/log/pods/kube-system_kube-apiserver-demo_14bdb317fab214c445c076df8385cb29/kube-apiserver/0.log
   ...

On SELinux-enabled platforms, the ``-Z`` flag can be used for many commands, like
``ls``, to show the SELinux context for an object. Here, we can see that the
container logs have the ``container_log_t`` type.

So these fluentbit containers need to be permitted to read files with this
``container_log_t`` label. How can we grant that permission? Actually, there
happens to be an SELinux domain called ``container_logreader_t`` that
containers are allowed to transition to, specified by policy provided by the
container-selinux package.

.. code-block:: console

   $ sudo seinfo -t container_logreader_t

   Types: 1
      container_logreader_t

Let's try using that:

.. code-block:: console

   $ kubectl patch daemonset logging-fluentbit -p '{"spec": {"template": {"spec": {"containers":[{"name": "fluent-bit", "securityContext": {"seLinuxOptions": {"type": "container_logreader_t"}}}]}}}}'
   daemonset.apps/logging-fluentbit patched
   $ kubectl rollout status daemonset logging-fluentbit
   daemon set "logging-fluentbit" successfully rolled out
   $ kubectl logs -l app.kubernetes.io/name=fluentbit

It still doesn't work. For more information, we need to go to the audit logs:

.. code-block:: console

   $ sudo tail -f /var/log/audit/audit.log | grep AVC
   type=AVC msg=audit(1656362206.779:8324): avc:  denied  { getattr } for  pid=52938 comm="flb-pipeline" path="/var/lib/docker/containers/ea544a7e64dc729c1f6fc52606253e70fd47954b7fd3ee8a2e5e5b715644ea39/ea544a7e64dc729c1f6fc52606253e70fd47954b7fd3ee8a2e5e5b715644ea39-json.log" dev="vda1" ino=201338977 scontext=system_u:system_r:container_logreader_t:s0:c291,c955 tcontext=system_u:object_r:container_var_lib_t:s0 tclass=file permissive=0

or

.. code-block:: console

   $ sudo ausearch -m AVC --start recent --just-one | grep AVC
   type=AVC msg=audit(1656361541.779:5840): avc:  denied  { getattr } for  pid=52938 comm="flb-pipeline" path="/var/lib/docker/containers/8ab96358bc771647242dbd04af0f2e0c27134c7a3a9d4597b5a818836c6df279/8ab96358bc771647242dbd04af0f2e0c27134c7a3a9d4597b5a818836c6df279-json.log" dev="vda1" ino=150999301 scontext=system_u:system_r:container_logreader_t:s0:c291,c955 tcontext=system_u:object_r:container_var_lib_t:s0 tclass=file permissive=0

Now we can finally see what's going on. A process with the
``container_logreader_t`` domain is trying to access (``getattr``) a file
(``tclass=file``) under ``/var/lib/docker/containers`` which has a type
``container_var_lib_t``. ``container_logreader_t`` can't open file with the
``container_var_lib_t`` type.  We can check this by checking what
``container_logreader_t`` is allowed to do for files:

.. code-block:: console

   $ sudo sesearch --allow | grep container_logreader_t | grep :file
   allow container_logreader_t auditd_log_t:file { getattr ioctl lock open read };
   allow container_logreader_t container_logreader_t:file { append getattr ioctl lock open read write };
   allow container_logreader_t container_logreader_t:filesystem associate;
   allow container_logreader_t logfile:file { getattr ioctl lock map open read };
   allow container_logreader_t proc_type:file { getattr ioctl lock open read };

Now we understand why the fluentbit pod mounts ``/var/lib/docker/containers``:
the log files in ``/var/log/containers`` are symlinks to ``/var/log/pods`` which
in turn are symlinks to ``/var/lib/docker/containers``. The fluentbit pod can't
follow a symlink on the host unless the target is also mounted on the container.
Docker `considers container log files to be application state
files <https://github.com/moby/moby/issues/21672#issuecomment-203715594>`_ and
discourages using them directly. They are created under the ``/var/lib/docker``
directory and therefore inherit the ``container_var_lib_t`` type, even though
the policy from container-selinux suggests they should be ``container_log_t``:

.. code-block:: console

   $ sudo semanage fcontext -l | grep '/var/lib/docker('
   /var/lib/docker(/.*)?                              all files          system_u:object_r:container_var_lib_t:s0
   $ sudo semanage fcontext -l | grep /var/lib/docker/containers.*log
   /var/lib/docker/containers/.*/.*\.log              all files          system_u:object_r:container_log_t:s0

We would have to run ``restorecon`` on ``/var/lib/docker/containers`` to change
the actual file context to match the policy.

Nevertheless, the easiest way for fluentbit on Kubernetes to consume these logs
is by mounting log directories as ``hostPath`` volumes and tailing the files.

First Draft Solution
====================

At this point we are beyond Kubernetes' ability to help us, because changing
the pod's ``seLinuxContext`` is not enough, and we need to work directly with the
host system to create a new policy. The first tool in the box is ``audit2allow``.
Let's use it to enumerate all the actions the fluentbit container is trying to
do. Let's also revert the container configuration back to where we started,
with no ``seLinuxOptions`` set, so that it will just run with the ``container_t``
label.

.. code-block:: console

   $ sudo grep AVC /var/log/audit/audit.log | tail -1 | tee -a avc.log
   type=AVC msg=audit(1656360224.779:1281): avc:  denied  { read } for  pid=25164 comm="flb-pipeline" name="containers" dev="vda1" ino=285212959 scontext=system_u:system_r:container_t:s0:c180,c507 tcontext=system_u:object_r:container_log_t:s0 tclass=dir permissive=0
   $ audit2allow -i avc.log -M logger
   ******************** IMPORTANT ***********************
   To make this policy package active, execute:

   semodule -i logger.pp
   $ cat logger.te

   module logger 1.0;

   require {
           type container_log_t;
           type container_t;
           class dir read;
   }

   #============= container_t ==============
   allow container_t container_log_t:dir read;
   $ sudo semodule -i logger.pp
   $ kubectl rollout restart daemonset logging-fluentbit
   daemonset.apps/logging-fluentbit restarted

In order to see the progress I'm making, I'm examining one AVC event at a time
and appending the events to a new file, creating a policy, installing it on the
host, and restarting the pod. We'll incrementally see that the container needs
to read log files with the ``container_log_t`` type, as well as to follow
symlinks for those files, then it needs to read directories and files with the
``container_var_lib_t`` type.

The trail may run dry, and the app still won't be working but there are no more
AVC events to be found. This may be because the access request is `silently
denied <https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html/security-enhanced_linux/sect-security-enhanced_linux-fixing_problems-possible_causes_of_silent_denials>`_.
To see these silent denials, disable ``dontaudit`` rules:

.. code-block:: console

   $ sudo semodule -DB

and keep going with ``audit2allow``.

The eventual result of the ``audit2allow`` iteration will be a policy file like
this:

.. code-block:: console

   $ cat logger.te

   module logger 1.0;

   require {
           type container_var_lib_t;
           type container_t;
           type container_log_t;
           class dir read;
           class lnk_file { getattr read };
           class file { getattr open read };
   }

   #============= container_t ==============

   allow container_t container_log_t:dir read;
   allow container_t container_log_t:lnk_file read;
   allow container_t container_log_t:lnk_file getattr;
   allow container_t container_var_lib_t:file { getattr open read };


This policy allows processes running with the ``container_t`` domain to read
files, symlinks and directories with the ``container_log_t`` label as well as to
access files with the ``container_var_lib_t`` label. We should now see the pod
able to successfully load and read the log files:

.. code-block:: console

   $ kubectl logs -l app.kubernetes.io/name=fluentbit
   [2022/06/27 21:05:31] [ info] [input:tail:tail.0] inotify_fs_add(): inode=297795882 watch_fd=9 name=/var/log/containers/kube-apiserver-demo_kube-system_kube-apiserver-79b1192098264baf2580c4709cf263facad0ff747de488348274b580cf58f52b.log
   [2022/06/27 21:05:31] [ info] [input:tail:tail.0] inotify_fs_add(): inode=272630437 watch_fd=10 name=/var/log/containers/kube-controller-manager-demo_kube-system_kube-controller-manager-1b67f7fa18a5641e003d5a92cd8668ed5e7878d3966d4f38f40e8407d1b3f07b.log
   [2022/06/27 21:05:31] [ info] [input:tail:tail.0] inotify_fs_add(): inode=171967056 watch_fd=11 name=/var/log/containers/kube-proxy-m9zc2_kube-system_kube-proxy-085e93b90ee09b952ea0156e45cb6d838a028ef56765b73fc295cbeaf0d1ec45.log
   [2022/06/27 21:05:31] [ info] [input:tail:tail.0] inotify_fs_add(): inode=104857841 watch_fd=12 name=/var/log/containers/kube-scheduler-demo_kube-system_kube-scheduler-a41028bc7eb05f8a07f44ce632a93b2d622ab3fa4d6f3d8bb6832f4f48ea8d6c.log

Now we have fully diagnosed why SELinux is preventing the fluentbit container
from doing its job, but we don't want to use this policy and call it a day.
This policy modifies the access rights of the ``container_t`` domain, giving
*every* container the ability to read container log files and container state
files. What we want is to create a new domain that containers can transition to.
Then only containers running with that domain label will have these special
privileges.

``audit2allow`` has gotten us far, but it can't conjure new domains, we have to
start writing it by hand.

A Better Solution
=================

First, we need to modify the module declaration, because we will be using the
policy developer tooling which includes some macros and templates. Change::

   module logger 1.0;

to::

   policy_module(logger, 1.0)

Then we need a brand new domain. Let's call it kube_logreader_t. Add it to the
require list::

   require {
           ...
           type kube_logreader_t;
           ...
   }

The container runtime needs the ability to transition into this new domain,
otherwise `containers are only allowed to transition to a small set of
domains <https://danwalsh.livejournal.com/81756.html>`_. We can use the
`container_domain_template`
`macro <https://github.com/containers/container-selinux/blob/ce85ca52a4c0d513fd9c0116cad64fa13f43861c/container.if#L849>`_
from the container-selinux policy::

   container_domain_template(kube_logreader)

This domain should inherit all the other special abilities that containers
have. This gives it the ability to do things like send a ``SIGCHLD`` signal when
it's ready to be reaped by its parent.

::

   virt_sandbox_domain(kube_logreader_t)
   corenet_unconfined(kube_logreader_t)

And this type should be granted all the filesystem permissions that we
discovered in our ``audit2allow`` journey. The final result is this::

   policy_module(logger, 1.0)

   require {
           type container_var_lib_t;
           type kube_logreader_t;
           type container_log_t;
           class dir read;
           class lnk_file { getattr read };
           class file { getattr open read };
   }

   #============= kube_logreader_t ==============

   container_domain_template(kube_logreader)
   virt_sandbox_domain(kube_logreader_t)
   corenet_unconfined(kube_logreader_t)

   allow kube_logreader_t container_log_t:dir read;
   allow kube_logreader_t container_log_t:lnk_file { getattr read };
   allow kube_logreader_t container_var_lib_t:file { getattr open read };


We need to compile this policy template and install it:

.. code-block:: console

   $ make -f /usr/share/selinux/devel/Makefile logger.pp
   Compiling targeted logger module
   Creating targeted logger.pp policy package
   rm tmp/logger.mod tmp/logger.mod.fc
   $ sudo semodule -i logger.pp

Now that we have a custom container domain, we need to tell the logger
application to use it. Banzai's logging operator exposes this functionality, we
just need to tell the Logging CRD about it:

.. code-block:: console

   $ cat logging.yaml
   apiVersion: logging.banzaicloud.io/v1beta1
   kind: Logging
   metadata:
     name: logging
   spec:
     fluentbit:
       security:
         securityContext:
           seLinuxOptions:
             type: kube_logreader_t
     fluentd:
       disablePvc: true
     controlNamespace: logging

Which results in a DaemonSet that manages a pod with the same seLinuxOptions:

.. code-block:: console

   $ kubectl apply -f logging.yaml
   logging.logging.banzaicloud.io/logging configured
   $ kubectl -n logging get daemonset logging-fluentbit -o jsonpath='{.spec.template.spec.containers[0].securityContext}' | jq .
   {
     "seLinuxOptions": {
       "type": "kube_logreader_t"
     }
   }

Conclusion
==========

When your applications get permission denied errors for actions that are part
of their core functionality and you see AVC events in your audit logs, you can
craft custom policies to support those applications without giving up on
SELinux entirely. Check out the `security-profiles-operator
<https://github.com/kubernetes-sigs/security-profiles-operator>`_ for a
Kubernetes-native way to install your custom policy on your nodes.
