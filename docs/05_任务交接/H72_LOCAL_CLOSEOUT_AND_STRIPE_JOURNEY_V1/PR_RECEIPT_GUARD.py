"""H72 PR-01: strict, non-mutating receipt verification.
Historical P0 receipt stays byte-frozen. New PR receipt binds the changed checker
and actual rerun captures; old source hashes alone cannot qualify current code.
"""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import json,re

OLD_RECEIPT_SHA = "1a0fef1472fe82206c6e57b072da66181dad02b4f6d6d273c9b60982e101483d"
AUDIT_SHA = "521a638f32e2366c83566074cd06d60015f06fe326839380cad8dba511eeefd6"
EXPECTED_COUNTS = {"safety":9,"regressions":74,"legacy_capture":11,"capture_lifecycle":9}
P0_LABELS = ("P0-ENV-01","P0-PRES-01","P0-SELF-01","P0-SAFE-01","P0-REG-01","P0-LEG-01","P0-LIFE-01")
PR_LABELS = ("PR-ENV-01","PR-PRES-01","PR-SELF-01","PR-SAFE-01","PR-REG-01","PR-LEG-01","PR-LIFE-01")

def time(s, need):
    need(isinstance(s,str) and s.strip(),"timestamp_missing")
    d=datetime.fromisoformat(s.replace("Z","+00:00"))
    need(d.tzinfo is not None, "timestamp_no_timezone")
    return d.astimezone(timezone.utc)

def test_count(raw:bytes):
    v=re.findall(rb"Ran\s+(\d+)\s+tests?\s+in\s+",raw)
    return int(v[-1]) if len(v)==1 else None

def expected_argv(label, g, canonical_root):
    py=str(g.AGENT_PYTHON)
    root=canonical_root
    base=root/"docs/05_任务交接"/g.PACK.name
    h68=root/"docs/05_任务交接/H68R_STRIPE_CHECKOUT_LOCAL_TRUST_REPAIR_V1/CHECK.py"
    h71=root/"docs/05_任务交接/H71R2_CAPTURE_FINALIZATION_GATE_REPAIR_V1"
    check=base/"CHECK.py"
    common={
      "ENV":[py,str(check),"environment"],
      "PRES":[py,str(check),"preservation"],
      "BUD":[py,str(check),"budget"],
      "SELF":[py,str(check),"p0-selftest"],
      "SAFE":[py,str(h68),"safety"],
      "REG":[py,"-m","unittest",*g.ORIGINAL_MODULES],
      "LEG":[py,str(h71/"PROBES_LEGACY.py")],
      "LIFE":[py,str(h71/"PROBES_LIFECYCLE.py")]
    }
    part=label.split("-")[1]
    return common[part]

def capture(g,item,folder,canonical_root,expected_count=None,after=None,before=None):
    g.need(isinstance(item,dict),"capture_row_invalid")
    label=item.get("label")
    g.need(isinstance(label,str) and re.fullmatch(r"(P0|PR|PR2)-[A-Z]+-01",label) is not None,"capture_label")
    g.need(item.get("command_argv")==expected_argv(label,g,canonical_root),"capture_command_argv:"+label)
    g.need(item.get("exit_code")==0,"capture_exit_code:"+label)
    paths={kind:folder/(label+"."+kind+".log") for kind in ("stdout","stderr")}
    paths["meta"]=folder/(label+".meta.json")
    for p in paths.values():g.need(p.is_file(),"capture_missing:"+str(p))
    meta=g.load_json(paths["meta"])
    g.need(meta.get("label")==label,"meta_label:"+label)
    g.need(meta.get("command_argv")==item["command_argv"],"meta_command_argv:"+label)
    g.need(Path(meta.get("working_directory","")).resolve()==canonical_root.resolve(),"meta_workdir:"+label)
    g.need(meta.get("exit_code")==0,"meta_exit_code:"+label)
    for kind in ("stdout","stderr"):
        actual=paths[kind].read_bytes()
        g.need(meta.get(kind+"_path")==paths[kind].name,"meta_output_path:"+label)
        g.need(g.digest(actual)==meta.get(kind+"_sha256")==item.get(kind+"_sha256"),"capture_output_sha:"+label)
        g.need(len(actual)==meta.get(kind+"_bytes")==item.get(kind+"_bytes"),"capture_output_size:"+label)
    g.need(g.digest_file(paths["meta"])==item.get("meta_sha256"),"capture_meta_sha:"+label)
    started=time(item.get("started_at_utc"),g.need)
    finished=time(item.get("finished_at_utc"),g.need)
    g.need(started<=finished,"capture_bad_interval:"+label)
    g.need(started==time(meta.get("started_at_utc"),g.need) and finished==time(meta.get("finished_at_utc"),g.need),"capture_time_mismatch:"+label)
    if after:g.need(started>=after,"capture_before_begin:"+label)
    if before:g.need(finished<=before,"capture_after_end:"+label)
    raw=paths["stdout"].read_bytes()+b"\n"+paths["stderr"].read_bytes()
    actual_count=test_count(raw)
    if expected_count is not None:
        g.need(actual_count==expected_count and item.get("test_count")==expected_count,"capture_test_count:"+label)
        g.need(re.search(rb"(?m)^OK\s*$",raw) is not None,"capture_tests_not_OK:"+label)
        g.need(b"FAILED (" not in raw and b"Traceback" not in raw,"capture_test_failure:"+label)
    else:
        g.need(item.get("test_count") is None,"unexpected_test_count:"+label)
    return {"label":label,"test_count":actual_count,"started":started,"finished":finished}

def historical(g):
    receipt=g.load_json(g.P0_RECEIPT)
    audit_path=g.PACK/"evidence/pre_review_20261115/AUDIT.json"
    g.need(g.digest_file(audit_path)==AUDIT_SHA,"audit_digest_changed")
    audit=g.load_json(audit_path)
    b=g.baseline()
    authorization=g.auth()
    g.need(receipt.get("schema")=="h72-p0-receipt/v1" and receipt.get("task_id")==g.PACK.name,"p0_receipt_identity")
    g.need(receipt.get("status") in ("PASS","PASS_WITH_LOCALE_DIFFERENCE_RECORDED"),"p0_receipt_status")
    g.need(receipt.get("baseline_head")==b["head"],"p0_baseline_head")
    g.need(receipt.get("baseline_sha256")==g.digest_file(g.PACK/"BASELINE.json"),"p0_baseline_sha")
    g.need(receipt.get("authorization_sha256")==g.digest_file(g.PACK/"AUTHORIZATION.json"),"p0_auth_sha")
    g.need(receipt.get("external_side_effects")=={"network":0,"installs":0,"services":0,"browser_actions":0,"payments":0},"p0_side_effects")
    g.need(receipt.get("test_counts")==EXPECTED_COUNTS,"p0_declared_counts")
    env=receipt.get("environment",{})
    g.need(env.get("executable")==str(g.AGENT_PYTHON),"p0_python")
    g.need(env.get("new_packages_installed")==0 and env.get("new_browsers_installed")==0,"p0_environment_modified")
    g.need(env.get("nested_import_probe",{}).get("assertion_tests_executed")==0,"p0_import_probe_assertions")
    g.need(receipt.get("preservation",{}).get("head")==b["head"],"p0_preservation_head")
    g.need(receipt.get("preservation",{}).get("protected_files")==len(b["protected"]) and
           receipt["preservation"].get("frozen_files")==len(b["frozen"]) and
           receipt["preservation"].get("reference_files")==len(b["references"]),"p0_preservation_counts")
    source=receipt.get("source_sha256")
    g.need(isinstance(source,dict) and set(source)=={"CHECK.py","RUN.py","tests_init.py","H68R_CHECK.py",
          "H71R2_PROBES_LEGACY.py","H71R2_PROBES_LIFECYCLE.py","capture_evidence.py"},"p0_source_set")
    g.need(source["CHECK.py"]==audit["source_snapshot"]["CHECK.py"] and
           source["RUN.py"]==audit["source_snapshot"]["RUN.py"],"p0_historical_source_binding")
    sourcemap={
      "tests_init.py":g.TESTS_INIT,
      "H68R_CHECK.py":g.ROOT/"docs/05_任务交接/H68R_STRIPE_CHECKOUT_LOCAL_TRUST_REPAIR_V1/CHECK.py",
      "H71R2_PROBES_LEGACY.py":g.ROOT/"docs/05_任务交接/H71R2_CAPTURE_FINALIZATION_GATE_REPAIR_V1/PROBES_LEGACY.py",
      "H71R2_PROBES_LIFECYCLE.py":g.ROOT/"docs/05_任务交接/H71R2_CAPTURE_FINALIZATION_GATE_REPAIR_V1/PROBES_LIFECYCLE.py",
      "capture_evidence.py":g.ROOT.parent/"localagent-common/skills/evaluator-executor-workflow/scripts/capture_evidence.py",
    }
    # Historical source stays sealed. The current CHECK/RUN are separately bound by PR receipt.
    for label,path in sourcemap.items():
        g.need(g.digest_file(path)==source[label],"p0_reference_source_changed:"+label)
    rows=receipt.get("commands")
    g.need(isinstance(rows,list) and len(rows)==len(P0_LABELS),"p0_missing_commands")
    g.need(tuple(x.get("label") for x in rows)==P0_LABELS,"p0_command_order_or_duplicate")
    orig=Path(receipt["environment"]["nested_import_probe"]["tests_path"][0]).parent
    g.need(orig==g.ROOT or orig.name==g.ROOT.name,"p0_canonical_repo")
    began=time(receipt.get("began_at_utc"),g.need)
    finished=time(receipt.get("completed_at_utc"),g.need)
    g.need(began<=finished,"p0_interval")
    observed={}
    last=began
    counts={"P0-SAFE-01":9,"P0-REG-01":74,"P0-LEG-01":11,"P0-LIFE-01":9}
    for item in rows:
        res=capture(g,item,g.PACK/"evidence/p0",orig,counts.get(item["label"]),after=last,before=finished)
        observed[res["label"]]=res["test_count"]
        last=res["finished"]
    g.need([observed[x] for x in counts]==list(counts.values()),"p0_observed_counts")
    # P0-REC is the extra self-check performed after receipt creation, not a mandatory assertion test.
    rc=receipt.get("receipt_check")
    g.need(isinstance(rc,dict) and rc.get("label")=="P0-REC-01" and rc.get("exit_code")==0,"p0_receipt_check")
    p=g.PACK/"evidence/p0/P0-REC-01.meta.json"
    m=g.load_json(p)
    g.need(m.get("command_argv")==[str(g.AGENT_PYTHON),str(orig/"docs/05_任务交接"/g.PACK.name/"CHECK.py"),"p0-receipt"],"p0_self_check_argv")
    g.need(g.digest_file(p)==rc.get("meta_sha256"),"p0_receipt_check_meta_sha")
    for kind in ("stdout","stderr"):
        f=p.parent/("P0-REC-01."+kind+".log")
        g.need(g.digest_file(f)==m.get(kind+"_sha256")==rc.get(kind+"_sha256") and
               f.stat().st_size==m.get(kind+"_bytes"),"p0_receipt_check_output")
    g.need(g.digest_file(g.P0_RECEIPT)==OLD_RECEIPT_SHA,"p0_receipt_original_digest_changed")
    return {"status":"HISTORICAL_EVIDENCE_INTACT_NOT_CURRENT_SOURCE","counts":dict(EXPECTED_COUNTS),
            "commands":len(rows),"source_current":False}

def repair(g):
    p=g.PACK/"PR_REPAIR_RECEIPT.json"
    g.need(p.is_file(),"repair_receipt_missing")
    r=g.load_json(p)
    g.need(r.get("schema")=="h72-pr-receipt/v1" and r.get("task_id")==g.PACK.name,
           "repair_receipt_identity")
    b=g.baseline()
    g.need(r.get("baseline_sha256")==g.digest_file(g.PACK/"BASELINE.json") and
           r.get("baseline_head")==b["head"],"repair_baseline_binding")
    g.need(r.get("authorization_sha256")==g.digest_file(g.PACK/"AUTHORIZATION.json"),"repair_original_auth_binding")
    addendum=g.PACK/"evidence/pr_reauthorization_20261115/AUTHORIZATION_ADDENDUM.json"
    g.need(r.get("reauthorization_sha256")==g.digest_file(addendum),"repair_reauth_binding")
    sources=r.get("source_sha256")
    expected={
      "CHECK.py":g.PACK/"CHECK.py",
      "RUN.py":g.PACK/"RUN.py",
      "PR_RECEIPT_GUARD.py":g.PACK/"PR_RECEIPT_GUARD.py",
      "PR_NEGATIVE_TESTS.py":g.PACK/"PR_NEGATIVE_TESTS.py",
      "PR_CAPTURE.py":g.PACK/"PR_CAPTURE.py",
      "tests_init.py":g.TESTS_INIT,
      "H68R_CHECK.py":g.ROOT/"docs/05_任务交接/H68R_STRIPE_CHECKOUT_LOCAL_TRUST_REPAIR_V1/CHECK.py",
      "H71R2_PROBES_LEGACY.py":g.ROOT/"docs/05_任务交接/H71R2_CAPTURE_FINALIZATION_GATE_REPAIR_V1/PROBES_LEGACY.py",
      "H71R2_PROBES_LIFECYCLE.py":g.ROOT/"docs/05_任务交接/H71R2_CAPTURE_FINALIZATION_GATE_REPAIR_V1/PROBES_LIFECYCLE.py",
      "capture_evidence.py":g.ROOT.parent/"localagent-common/skills/evaluator-executor-workflow/scripts/capture_evidence.py",
    }
    g.need(isinstance(sources,dict) and set(sources)==set(expected),"repair_source_set")
    for k,path in expected.items():
        g.need(g.digest_file((g.PACK/"versions/pr_guard_v1"/k) if k in {"CHECK.py","PR_RECEIPT_GUARD.py"} else path)==sources[k],"repair_historical_source_stale:"+k)
    g.need(r.get("product_sha256")==b["allowed_product_initial"],
           "repair_original_product_snapshot_changed")
    g.need(r.get("test_counts")==EXPECTED_COUNTS,"repair_declared_counts")
    g.need(r.get("external_side_effects")=={"network":0,"installs":0,"services":0,"browser_actions":0,"payments":0},
           "repair_external_effects")
    rows=r.get("commands")
    g.need(isinstance(rows,list) and len(rows)==len(PR_LABELS),"repair_missing_commands")
    g.need(tuple(x.get("label") for x in rows)==PR_LABELS,"repair_command_labels")
    began=time(r.get("began_at_utc"),g.need)
    end=time(r.get("completed_at_utc"),g.need)
    g.need(began<=end,"repair_bad_interval")
    last=began
    counts={"PR-SELF-01":r.get("negative_fixture_tests"),"PR-SAFE-01":9,"PR-REG-01":74,
            "PR-LEG-01":11,"PR-LIFE-01":9}
    g.need(type(counts["PR-SELF-01"]) is int and counts["PR-SELF-01"]>=9,"repair_negative_tests_missing")
    for item in rows:
        x=capture(g,item,g.PACK/"evidence/pr_repair_20261115",g.ROOT,counts.get(item["label"]),after=last,before=end)
        last=x["finished"]
    g.need(r.get("guardrail_status")=="PASS_WITH_NEGATIVE_FIXTURES","repair_gate_not_pass")
    refresh_current(g)
    return {"status":"PASS","historical_evidence":"INTACT","updated_guardrail_status":"PASS",
            "negative_fixture_tests":counts["PR-SELF-01"],"test_counts":EXPECTED_COUNTS}


def refresh_current(g):
    # Append-only P1 source repair; PR-v1 and original P0 receipts remain immutable.
    f=g.PACK/"evidence/p1/PR2_GUARD_REFRESH.json"
    g.need(f.is_file(),"pr2_guard_refresh_missing")
    doc=g.load_json(f)
    g.need(doc.get("schema")=="h72-pr2-guard-refresh/v1" and
           doc.get("task_id")==g.PACK.name,"pr2_identity")
    g.need(doc.get("prior_receipt_sha256")=="f2aa72bb48bc653e0db76a732ad95b551c70af4ae7eaea40440be71955f7c93d",
           "pr2_prior_receipt_reference")
    g.need(g.digest_file(g.PACK/"PR_REPAIR_RECEIPT.json")==doc["prior_receipt_sha256"],
           "pr2_prior_receipt_modified")
    files={
      "CHECK.py":g.PACK/"CHECK.py",
      "PR_RECEIPT_GUARD.py":g.PACK/"PR_RECEIPT_GUARD.py",
      "PR_NEGATIVE_TESTS.py":g.PACK/"PR_NEGATIVE_TESTS.py",
      "PR_CAPTURE.py":g.PACK/"PR_CAPTURE.py",
      "RUN.py":g.PACK/"RUN.py",
      "tests_init.py":g.TESTS_INIT,
    }
    sources=doc.get("source_sha256")
    g.need(isinstance(sources,dict) and set(sources)==set(files),"pr2_source_set")
    for name,path in files.items():
        source_path=(g.PACK/"versions/pr_guard_v2"/name) if name in {"CHECK.py","PR_RECEIPT_GUARD.py"} else path
        g.need(g.digest_file(source_path)==sources[name],"pr2_historical_source_stale:"+name)
    b=g.baseline()
    g.need(doc.get("product_sha256")==b["allowed_product_initial"],
           "pr2_product_snapshot_changed")
    labels=("PR2-PRES-01","PR2-BUD-01","PR2-SELF-01")
    rows=doc.get("commands")
    g.need(isinstance(rows,list) and tuple(x.get("label") for x in rows)==labels,
           "pr2_mandatory_commands")
    began=time(doc.get("began_at_utc"),g.need)
    finish=time(doc.get("completed_at_utc"),g.need)
    g.need(began<=finish,"pr2_bad_interval")
    last=began
    for row in rows:
        count=16 if row["label"]=="PR2-SELF-01" else None
        item=capture(g,row,g.PACK/"evidence/p1/guard_refresh_20261115",g.ROOT,count,after=last,before=finish)
        last=item["finished"]
    g.need(doc.get("status")=="PASS_WITH_SOURCE_REFRESH","pr2_status")
    verify_product_patch(g)
    return {"status":"PASS","source_current":True,"guard_refresh_commands":len(rows)}

def verify_product_patch(g):
    f=g.PACK/"evidence/p1/PR3_PRODUCT_PATCH_RECEIPT.json"
    g.need(f.is_file(),"pr3_product_patch_receipt_missing")
    doc=g.load_json(f)
    g.need(doc.get("schema")=="h72-pr3-product-patch/v1" and
           doc.get("task_id")==g.PACK.name,"pr3_identity")
    for name,sha in doc.get("source_sha256",{}).items():
        permitted={
          "CHECK.py":g.PACK/"CHECK.py",
          "PR_RECEIPT_GUARD.py":g.PACK/"PR_RECEIPT_GUARD.py",
          "PR_NEGATIVE_TESTS.py":g.PACK/"PR_NEGATIVE_TESTS.py",
          "PR_CAPTURE.py":g.PACK/"PR_CAPTURE.py",
          "tests/test_h72_stripe_journey.py":g.ROOT/"tests/test_h72_stripe_journey.py",
          "src/agentic_payment_experiment/adapters/stripe_checkout.py":g.ROOT/"src/agentic_payment_experiment/adapters/stripe_checkout.py",
          "src/agentic_payment_experiment/stripe_checkout_lab.py":g.ROOT/"src/agentic_payment_experiment/stripe_checkout_lab.py",
          "scripts/validation/stripe_checkout_lab.py":g.ROOT/"scripts/validation/stripe_checkout_lab.py",
        }
        g.need(name in permitted,"pr3_extra_untrusted_source:"+name)
        source=(g.PACK/"versions/pr_guard_v3"/name) if name in {"CHECK.py","PR_RECEIPT_GUARD.py"} else permitted[name]
        g.need(g.digest_file(source)==sha,"pr3_historical_source_stale:"+name)
    g.need(set(doc.get("source_sha256",{}))==set(permitted),"pr3_source_missing")
    b=g.baseline()
    g.need(doc.get("product_sha256")=={rel:g.digest_file(g.ROOT/rel) for rel in b["allowed_product_initial"]},
           "pr3_product_binding_changed")
    g.need(doc.get("baseline_sha256")==g.digest_file(g.PACK/"BASELINE.json"),"pr3_baseline_changed")
    g.need(doc.get("authorization_sha256")==g.digest_file(g.PACK/"AUTHORIZATION.json"),"pr3_auth_changed")
    g.need(doc.get("reauthorization_sha256")==
           g.digest_file(g.PACK/"evidence/pr_reauthorization_20261115/AUTHORIZATION_ADDENDUM.json"),
           "pr3_reauth_changed")
    labels=("PR3-NEW-01","PR3-SAFE-01","PR3-REG-01","PR3-LEG-01","PR3-LIFE-01","PR3-PRES-01")
    rows=doc.get("commands")
    g.need(isinstance(rows,list) and tuple(x.get("label") for x in rows)==labels,
           "pr3_missing_commands")
    began=time(doc.get("began_at_utc"),g.need)
    end=time(doc.get("completed_at_utc"),g.need)
    last=began
    counts={"PR3-NEW-01":6,"PR3-SAFE-01":9,"PR3-REG-01":74,"PR3-LEG-01":11,"PR3-LIFE-01":9}
    for row in rows:
        expected=counts.get(row["label"])
        g.need(isinstance(row.get("command_argv"),list) and row.get("command_argv"),"pr3_argv_missing")
        # command identity and exact argv are bound to the captured metadata.
        meta=g.PACK/"evidence/p1/product_patch_20261115"/(row["label"]+".meta.json")
        stdout=g.PACK/"evidence/p1/product_patch_20261115"/(row["label"]+".stdout.log")
        stderr=g.PACK/"evidence/p1/product_patch_20261115"/(row["label"]+".stderr.log")
        g.need(meta.is_file() and stdout.is_file() and stderr.is_file(),"pr3_evidence_missing")
        m=g.load_json(meta)
        g.need(m.get("label")==row["label"] and m.get("command_argv")==row["command_argv"],
               "pr3_argv_mismatch")
        g.need(m.get("exit_code")==row.get("exit_code")==0,"pr3_exit")
        g.need(g.digest_file(meta)==row.get("meta_sha256"),"pr3_meta_hash")
        for kind,log in (("stdout",stdout),("stderr",stderr)):
            g.need(g.digest_file(log)==m.get(kind+"_sha256")==row.get(kind+"_sha256") and
                   log.stat().st_size==m.get(kind+"_bytes")==row.get(kind+"_bytes"),"pr3_output_integrity")
        st=time(m.get("started_at_utc"),g.need)
        fin=time(m.get("finished_at_utc"),g.need)
        g.need(last<=st<=fin<=end,"pr3_time_chain")
        last=fin
        if expected is not None:
            raw=stdout.read_bytes()+b"\n"+stderr.read_bytes()
            count=test_count(raw)
            g.need(count==expected and row.get("test_count")==expected and
                   re.search(rb"(?m)^OK\s*$",raw) is not None,"pr3_observed_count")
    g.need(doc.get("status")=="PASS_WITH_PRODUCT_PATCH","pr3_guard_status")
    verify_resume_source_refresh(g)
    return {"status":"PASS","changed_product_measured":True}

def verify_resume_source_refresh(g):
    """Append-only current-source attestation; older receipts remain immutable."""
    record=g.PACK/"evidence/resumed_20261115/PR4_SOURCE_REFRESH.json"
    g.need(record.is_file(),"pr4_refresh_required")
    doc=g.load_json(record)
    g.need(doc.get("schema")=="h72-pr4-source-refresh/v1" and
           doc.get("task_id")==g.PACK.name,"pr4_identity")
    previous={
      "P0_RECEIPT.json":g.PACK/"P0_RECEIPT.json",
      "PR_REPAIR_RECEIPT.json":g.PACK/"PR_REPAIR_RECEIPT.json",
      "PR2_GUARD_REFRESH.json":g.PACK/"evidence/p1/PR2_GUARD_REFRESH.json",
      "PR3_PRODUCT_PATCH_RECEIPT.json":g.PACK/"evidence/p1/PR3_PRODUCT_PATCH_RECEIPT.json",
    }
    g.need(doc.get("prior_receipt_sha256")=={k:g.digest_file(p) for k,p in previous.items()},
           "pr4_prior_receipt_changed")
    latest={
      "CHECK.py":g.PACK/"CHECK.py",
      "PR_RECEIPT_GUARD.py":g.PACK/"PR_RECEIPT_GUARD.py",
      "EXTERNAL_EVIDENCE.py":g.PACK/"EXTERNAL_EVIDENCE.py",
      "OBSERVE.py":g.PACK/"OBSERVE.py",
      "runtime/h72_four_journeys.py":g.PACK/"runtime/h72_four_journeys.py",
      "runtime/h72_run_common.py":g.PACK/"runtime/h72_run_common.py",
      "runtime/h72_merchant_server.py":g.PACK/"runtime/h72_merchant_server.py",
      "runtime/h72_card_form.py":g.PACK/"runtime/h72_card_form.py",
      "runtime/h72_cdp_ws.py":g.PACK/"runtime/h72_cdp_ws.py",
      "tests/test_h72_stripe_journey.py":g.ROOT/"tests/test_h72_stripe_journey.py",
      "src/agentic_payment_experiment/adapters/stripe_checkout.py":
          g.ROOT/"src/agentic_payment_experiment/adapters/stripe_checkout.py",
    }
    actual=doc.get("source_sha256")
    g.need(isinstance(actual,dict) and set(actual)==set(latest),"pr4_source_keys")
    for key,path in latest.items():
        g.need(g.digest_file(path)==actual[key],"pr4_source_stale:"+key)
    g.need(doc.get("executor_candidate_final_sha256")==
           g.digest_file(g.PACK/"evidence/resumed_20261115/FINAL.json"),
           "pr4_real_external_result_changed")
    return {"status":"PASS","current_source_bound":True}
