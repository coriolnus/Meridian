# ÜRETİLMİŞ — ops/apisix_tf_uret.py; kaynak deploy/apisix/routes.yaml. Elle düzenlenmez.

import {
  to = apisix_consumer_group.filo
  id = "filo"
}

import {
  to = apisix_consumer.bot_bekci
  id = "bot_bekci"
}

import {
  to = apisix_consumer.bot_karne
  id = "bot_karne"
}

import {
  to = apisix_consumer.bot_sef
  id = "bot_sef"
}

import {
  to = apisix_consumer.motor_meridian
  id = "motor_meridian"
}

import {
  to = apisix_route.llm_danisma
  id = "llm-danisma"
}

import {
  to = apisix_route.fmp_veri
  id = "fmp-veri"
}

import {
  to = apisix_route.metrics_dis
  id = "metrics-dis"
}

import {
  to = apisix_route.pano_ingress
  id = "pano-ingress"
}

import {
  to = apisix_route.llm_hizli
  id = "llm-hizli"
}

import {
  to = apisix_route.llm_models
  id = "llm-models"
}

