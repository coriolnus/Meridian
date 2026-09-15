# ÜRETİLMİŞ — ops/apisix_tf_uret.py; kaynak deploy/apisix/routes.yaml. Elle düzenlenmez.

import {
  to = apisix_consumer_group.filo
  id = "filo"
  provider = apisix
}

import {
  to = apisix_consumer.bot_bekci
  id = "bot_bekci"
  provider = apisix
}

import {
  to = apisix_consumer.bot_karne
  id = "bot_karne"
  provider = apisix
}

import {
  to = apisix_consumer.bot_sef
  id = "bot_sef"
  provider = apisix
}

import {
  to = apisix_consumer.motor_meridian
  id = "motor_meridian"
  provider = apisix
}

import {
  to = apisix_route.llm_danisma
  id = "llm-danisma"
  provider = apisix
}

import {
  to = apisix_route.fmp_veri
  id = "fmp-veri"
  provider = apisix
}

import {
  to = apisix_route.metrics_dis
  id = "metrics-dis"
  provider = apisix
}

import {
  to = apisix_route.pano_ingress
  id = "pano-ingress"
  provider = apisix
}

import {
  to = apisix_route.llm_hizli
  id = "llm-hizli"
  provider = apisix
}

import {
  to = apisix_route.llm_models
  id = "llm-models"
  provider = apisix
}

