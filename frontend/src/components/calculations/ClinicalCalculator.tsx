// ABOUTME: Clinical calculator component with pre-built medical calculations
// ABOUTME: Provides interactive forms for common clinical calculations like BMI, BSA, eGFR

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Calculator, 
  Activity, 
  Heart, 
  Droplets,
  TrendingUp,
  AlertCircle,
  Info,
  Copy,
  RotateCcw
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

interface CalculationResult {
  value: number | string;
  unit: string;
  interpretation?: string;
  reference?: string;
  warning?: string;
}

export function ClinicalCalculator() {
  const { toast } = useToast();

  // BMI Calculator State
  const [bmiData, setBmiData] = useState({
    weight: '',
    weightUnit: 'kg',
    height: '',
    heightUnit: 'cm'
  });
  const [bmiResult, setBmiResult] = useState<CalculationResult | null>(null);

  // BSA Calculator State
  const [bsaData, setBsaData] = useState({
    weight: '',
    weightUnit: 'kg',
    height: '',
    heightUnit: 'cm',
    formula: 'dubois'
  });
  const [bsaResult, setBsaResult] = useState<CalculationResult | null>(null);

  // eGFR Calculator State
  const [egfrData, setEgfrData] = useState({
    creatinine: '',
    creatinineUnit: 'mg/dL',
    age: '',
    sex: '',
    race: 'other',
    formula: 'ckd-epi'
  });
  const [egfrResult, setEgfrResult] = useState<CalculationResult | null>(null);

  // Creatinine Clearance State
  const [crclData, setCrclData] = useState({
    creatinine: '',
    age: '',
    weight: '',
    sex: ''
  });
  const [crclResult, setCrclResult] = useState<CalculationResult | null>(null);

  // Child-Pugh Score State
  const [childPughData, setChildPughData] = useState({
    bilirubin: '',
    albumin: '',
    inr: '',
    ascites: 'none',
    encephalopathy: 'none'
  });
  const [childPughResult, setChildPughResult] = useState<CalculationResult | null>(null);

  // MELD Score State
  const [meldData, setMeldData] = useState({
    creatinine: '',
    bilirubin: '',
    inr: '',
    dialysis: false
  });
  const [meldResult, setMeldResult] = useState<CalculationResult | null>(null);

  // Calculate BMI
  const calculateBMI = () => {
    const weight = parseFloat(bmiData.weight);
    const height = parseFloat(bmiData.height);

    if (!weight || !height) {
      toast({
        title: 'Invalid Input',
        description: 'Please enter valid weight and height',
        variant: 'destructive'
      });
      return;
    }

    // Convert to kg and cm if needed
    const weightKg = bmiData.weightUnit === 'lb' ? weight * 0.453592 : weight;
    const heightCm = bmiData.heightUnit === 'in' ? height * 2.54 : height;

    const heightM = heightCm / 100;
    const bmi = weightKg / (heightM * heightM);

    let interpretation = '';
    if (bmi < 18.5) interpretation = 'Underweight';
    else if (bmi < 25) interpretation = 'Normal weight';
    else if (bmi < 30) interpretation = 'Overweight';
    else interpretation = 'Obese';

    setBmiResult({
      value: bmi.toFixed(1),
      unit: 'kg/m²',
      interpretation,
      reference: 'WHO Classification'
    });
  };

  // Calculate BSA
  const calculateBSA = () => {
    const weight = parseFloat(bsaData.weight);
    const height = parseFloat(bsaData.height);

    if (!weight || !height) {
      toast({
        title: 'Invalid Input',
        description: 'Please enter valid weight and height',
        variant: 'destructive'
      });
      return;
    }

    // Convert to kg and cm if needed
    const weightKg = bsaData.weightUnit === 'lb' ? weight * 0.453592 : weight;
    const heightCm = bsaData.heightUnit === 'in' ? height * 2.54 : height;

    let bsa = 0;
    if (bsaData.formula === 'dubois') {
      // DuBois formula
      bsa = 0.007184 * Math.pow(weightKg, 0.425) * Math.pow(heightCm, 0.725);
    } else if (bsaData.formula === 'mosteller') {
      // Mosteller formula
      bsa = Math.sqrt((heightCm * weightKg) / 3600);
    }

    setBsaResult({
      value: bsa.toFixed(2),
      unit: 'm²',
      interpretation: `Formula: ${bsaData.formula.charAt(0).toUpperCase() + bsaData.formula.slice(1)}`,
      reference: 'Normal range: 1.6-2.0 m²'
    });
  };

  // Calculate eGFR
  const calculateEGFR = () => {
    const creatinine = parseFloat(egfrData.creatinine);
    const age = parseFloat(egfrData.age);

    if (!creatinine || !age || !egfrData.sex) {
      toast({
        title: 'Invalid Input',
        description: 'Please enter all required values',
        variant: 'destructive'
      });
      return;
    }

    // Convert to mg/dL if needed
    const creatinineMgDl = egfrData.creatinineUnit === 'umol/L' ? creatinine / 88.4 : creatinine;

    let egfr = 0;
    if (egfrData.formula === 'ckd-epi') {
      // CKD-EPI formula
      const kappa = egfrData.sex === 'F' ? 0.7 : 0.9;
      const alpha = egfrData.sex === 'F' ? -0.329 : -0.411;
      const sexFactor = egfrData.sex === 'F' ? 1.018 : 1.0;
      const raceFactor = egfrData.race === 'black' ? 1.159 : 1.0;

      const minCrKappa = Math.min(creatinineMgDl / kappa, 1);
      const maxCrKappa = Math.max(creatinineMgDl / kappa, 1);

      egfr = 141 * Math.pow(minCrKappa, alpha) * Math.pow(maxCrKappa, -1.209) *
             Math.pow(0.993, age) * sexFactor * raceFactor;
    } else if (egfrData.formula === 'mdrd') {
      // MDRD formula
      const sexFactor = egfrData.sex === 'F' ? 0.742 : 1.0;
      const raceFactor = egfrData.race === 'black' ? 1.212 : 1.0;

      egfr = 175 * Math.pow(creatinineMgDl, -1.154) * Math.pow(age, -0.203) *
             sexFactor * raceFactor;
    }

    let interpretation = '';
    if (egfr >= 90) interpretation = 'G1: Normal or high';
    else if (egfr >= 60) interpretation = 'G2: Mildly decreased';
    else if (egfr >= 45) interpretation = 'G3a: Mildly to moderately decreased';
    else if (egfr >= 30) interpretation = 'G3b: Moderately to severely decreased';
    else if (egfr >= 15) interpretation = 'G4: Severely decreased';
    else interpretation = 'G5: Kidney failure';

    setEgfrResult({
      value: egfr.toFixed(1),
      unit: 'mL/min/1.73m²',
      interpretation,
      reference: 'KDIGO CKD Classification',
      warning: egfr < 60 ? 'Consider nephrology referral' : undefined
    });
  };

  // Calculate Creatinine Clearance
  const calculateCrCl = () => {
    const creatinine = parseFloat(crclData.creatinine);
    const age = parseFloat(crclData.age);
    const weight = parseFloat(crclData.weight);

    if (!creatinine || !age || !weight || !crclData.sex) {
      toast({
        title: 'Invalid Input',
        description: 'Please enter all required values',
        variant: 'destructive'
      });
      return;
    }

    const sexFactor = crclData.sex === 'F' ? 0.85 : 1.0;
    const crcl = ((140 - age) * weight * sexFactor) / (72 * creatinine);

    let interpretation = '';
    if (crcl >= 90) interpretation = 'Normal';
    else if (crcl >= 60) interpretation = 'Mild reduction';
    else if (crcl >= 30) interpretation = 'Moderate reduction';
    else if (crcl >= 15) interpretation = 'Severe reduction';
    else interpretation = 'Kidney failure';

    setCrclResult({
      value: crcl.toFixed(1),
      unit: 'mL/min',
      interpretation,
      reference: 'Cockcroft-Gault Equation'
    });
  };

  // Calculate Child-Pugh Score
  const calculateChildPugh = () => {
    const bilirubin = parseFloat(childPughData.bilirubin);
    const albumin = parseFloat(childPughData.albumin);
    const inr = parseFloat(childPughData.inr);

    if (!bilirubin || !albumin || !inr) {
      toast({
        title: 'Invalid Input',
        description: 'Please enter all required values',
        variant: 'destructive'
      });
      return;
    }

    let score = 0;

    // Bilirubin
    if (bilirubin < 2) score += 1;
    else if (bilirubin <= 3) score += 2;
    else score += 3;

    // Albumin
    if (albumin > 3.5) score += 1;
    else if (albumin >= 2.8) score += 2;
    else score += 3;

    // INR
    if (inr < 1.7) score += 1;
    else if (inr <= 2.3) score += 2;
    else score += 3;

    // Ascites
    if (childPughData.ascites === 'none') score += 1;
    else if (childPughData.ascites === 'mild') score += 2;
    else score += 3;

    // Encephalopathy
    if (childPughData.encephalopathy === 'none') score += 1;
    else if (childPughData.encephalopathy === 'grade_1_2') score += 2;
    else score += 3;

    let childClass = '';
    let prognosis = '';
    if (score <= 6) {
      childClass = 'A';
      prognosis = '1-year survival: 100%, 2-year survival: 85%';
    } else if (score <= 9) {
      childClass = 'B';
      prognosis = '1-year survival: 81%, 2-year survival: 57%';
    } else {
      childClass = 'C';
      prognosis = '1-year survival: 45%, 2-year survival: 35%';
    }

    setChildPughResult({
      value: `Class ${childClass} (Score: ${score})`,
      unit: 'points',
      interpretation: prognosis,
      reference: 'Child-Pugh Classification'
    });
  };

  // Calculate MELD Score
  const calculateMELD = () => {
    const creatinine = parseFloat(meldData.creatinine);
    const bilirubin = parseFloat(meldData.bilirubin);
    const inr = parseFloat(meldData.inr);

    if (!creatinine || !bilirubin || !inr) {
      toast({
        title: 'Invalid Input',
        description: 'Please enter all required values',
        variant: 'destructive'
      });
      return;
    }

    // Apply minimum values
    const cr = Math.max(creatinine, 1.0);
    const bili = Math.max(bilirubin, 1.0);
    const inrVal = Math.max(inr, 1.0);

    // Cap creatinine at 4.0 if on dialysis
    const crFinal = meldData.dialysis ? Math.min(cr, 4.0) : cr;

    const meld = 10 * (0.957 * Math.log(crFinal) + 
                       0.378 * Math.log(bili) + 
                       1.12 * Math.log(inrVal)) + 6.43;

    const meldScore = Math.round(Math.max(6, Math.min(40, meld)));

    let mortality = '';
    if (meldScore <= 9) mortality = '3-month mortality: 1.9%';
    else if (meldScore <= 19) mortality = '3-month mortality: 6.0%';
    else if (meldScore <= 29) mortality = '3-month mortality: 19.6%';
    else if (meldScore <= 39) mortality = '3-month mortality: 52.6%';
    else mortality = '3-month mortality: 71.3%';

    setMeldResult({
      value: meldScore,
      unit: 'points',
      interpretation: mortality,
      reference: 'MELD Score (Model for End-Stage Liver Disease)'
    });
  };

  const copyResult = (result: CalculationResult) => {
    const text = `${result.value} ${result.unit}${result.interpretation ? ` (${result.interpretation})` : ''}`;
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied',
      description: 'Result copied to clipboard'
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Clinical Calculators</h2>
        <p className="text-muted-foreground">
          Common medical calculations for clinical trials
        </p>
      </div>

      <Tabs defaultValue="basic" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="basic">Basic</TabsTrigger>
          <TabsTrigger value="renal">Renal</TabsTrigger>
          <TabsTrigger value="hepatic">Hepatic</TabsTrigger>
        </TabsList>

        <TabsContent value="basic" className="space-y-4">
          {/* BMI Calculator */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Body Mass Index (BMI)
              </CardTitle>
              <CardDescription>
                Calculate BMI from height and weight
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Weight</Label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      value={bmiData.weight}
                      onChange={(e) => setBmiData({ ...bmiData, weight: e.target.value })}
                      placeholder="Enter weight"
                    />
                    <Select
                      value={bmiData.weightUnit}
                      onValueChange={(value) => setBmiData({ ...bmiData, weightUnit: value })}
                    >
                      <SelectTrigger className="w-20">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="kg">kg</SelectItem>
                        <SelectItem value="lb">lb</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label>Height</Label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      value={bmiData.height}
                      onChange={(e) => setBmiData({ ...bmiData, height: e.target.value })}
                      placeholder="Enter height"
                    />
                    <Select
                      value={bmiData.heightUnit}
                      onValueChange={(value) => setBmiData({ ...bmiData, heightUnit: value })}
                    >
                      <SelectTrigger className="w-20">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="cm">cm</SelectItem>
                        <SelectItem value="in">in</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <Button onClick={calculateBMI} className="w-full">
                <Calculator className="mr-2 h-4 w-4" />
                Calculate BMI
              </Button>

              {bmiResult && (
                <Alert>
                  <AlertDescription>
                    <div className="flex justify-between items-start">
                      <div className="space-y-1">
                        <div className="text-2xl font-bold">
                          {bmiResult.value} {bmiResult.unit}
                        </div>
                        <div className="text-sm">{bmiResult.interpretation}</div>
                        <div className="text-xs text-muted-foreground">{bmiResult.reference}</div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyResult(bmiResult)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* BSA Calculator */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Body Surface Area (BSA)
              </CardTitle>
              <CardDescription>
                Calculate BSA for drug dosing
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Weight</Label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      value={bsaData.weight}
                      onChange={(e) => setBsaData({ ...bsaData, weight: e.target.value })}
                      placeholder="Enter weight"
                    />
                    <Select
                      value={bsaData.weightUnit}
                      onValueChange={(value) => setBsaData({ ...bsaData, weightUnit: value })}
                    >
                      <SelectTrigger className="w-20">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="kg">kg</SelectItem>
                        <SelectItem value="lb">lb</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label>Height</Label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      value={bsaData.height}
                      onChange={(e) => setBsaData({ ...bsaData, height: e.target.value })}
                      placeholder="Enter height"
                    />
                    <Select
                      value={bsaData.heightUnit}
                      onValueChange={(value) => setBsaData({ ...bsaData, heightUnit: value })}
                    >
                      <SelectTrigger className="w-20">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="cm">cm</SelectItem>
                        <SelectItem value="in">in</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <div>
                <Label>Formula</Label>
                <Select
                  value={bsaData.formula}
                  onValueChange={(value) => setBsaData({ ...bsaData, formula: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="dubois">DuBois</SelectItem>
                    <SelectItem value="mosteller">Mosteller</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button onClick={calculateBSA} className="w-full">
                <Calculator className="mr-2 h-4 w-4" />
                Calculate BSA
              </Button>

              {bsaResult && (
                <Alert>
                  <AlertDescription>
                    <div className="flex justify-between items-start">
                      <div className="space-y-1">
                        <div className="text-2xl font-bold">
                          {bsaResult.value} {bsaResult.unit}
                        </div>
                        <div className="text-sm">{bsaResult.interpretation}</div>
                        <div className="text-xs text-muted-foreground">{bsaResult.reference}</div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyResult(bsaResult)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="renal" className="space-y-4">
          {/* eGFR Calculator */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Droplets className="h-5 w-5" />
                Estimated GFR (eGFR)
              </CardTitle>
              <CardDescription>
                Calculate kidney function using CKD-EPI or MDRD
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Creatinine</Label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      step="0.1"
                      value={egfrData.creatinine}
                      onChange={(e) => setEgfrData({ ...egfrData, creatinine: e.target.value })}
                      placeholder="Enter creatinine"
                    />
                    <Select
                      value={egfrData.creatinineUnit}
                      onValueChange={(value) => setEgfrData({ ...egfrData, creatinineUnit: value })}
                    >
                      <SelectTrigger className="w-24">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="mg/dL">mg/dL</SelectItem>
                        <SelectItem value="umol/L">μmol/L</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label>Age (years)</Label>
                  <Input
                    type="number"
                    value={egfrData.age}
                    onChange={(e) => setEgfrData({ ...egfrData, age: e.target.value })}
                    placeholder="Enter age"
                  />
                </div>

                <div>
                  <Label>Sex</Label>
                  <Select
                    value={egfrData.sex}
                    onValueChange={(value) => setEgfrData({ ...egfrData, sex: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select sex" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="M">Male</SelectItem>
                      <SelectItem value="F">Female</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Race</Label>
                  <Select
                    value={egfrData.race}
                    onValueChange={(value) => setEgfrData({ ...egfrData, race: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="black">Black</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Formula</Label>
                  <Select
                    value={egfrData.formula}
                    onValueChange={(value) => setEgfrData({ ...egfrData, formula: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ckd-epi">CKD-EPI</SelectItem>
                      <SelectItem value="mdrd">MDRD</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button onClick={calculateEGFR} className="w-full">
                <Calculator className="mr-2 h-4 w-4" />
                Calculate eGFR
              </Button>

              {egfrResult && (
                <Alert variant={egfrResult.warning ? 'destructive' : 'default'}>
                  <AlertDescription>
                    <div className="flex justify-between items-start">
                      <div className="space-y-1">
                        <div className="text-2xl font-bold">
                          {egfrResult.value} {egfrResult.unit}
                        </div>
                        <div className="text-sm">{egfrResult.interpretation}</div>
                        <div className="text-xs text-muted-foreground">{egfrResult.reference}</div>
                        {egfrResult.warning && (
                          <div className="text-sm font-medium flex items-center gap-1 mt-2">
                            <AlertCircle className="h-4 w-4" />
                            {egfrResult.warning}
                          </div>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyResult(egfrResult)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="hepatic" className="space-y-4">
          {/* Child-Pugh Score */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Heart className="h-5 w-5" />
                Child-Pugh Score
              </CardTitle>
              <CardDescription>
                Assess severity of liver disease
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Bilirubin (mg/dL)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={childPughData.bilirubin}
                    onChange={(e) => setChildPughData({ ...childPughData, bilirubin: e.target.value })}
                    placeholder="Enter bilirubin"
                  />
                </div>

                <div>
                  <Label>Albumin (g/dL)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={childPughData.albumin}
                    onChange={(e) => setChildPughData({ ...childPughData, albumin: e.target.value })}
                    placeholder="Enter albumin"
                  />
                </div>

                <div>
                  <Label>INR</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={childPughData.inr}
                    onChange={(e) => setChildPughData({ ...childPughData, inr: e.target.value })}
                    placeholder="Enter INR"
                  />
                </div>

                <div>
                  <Label>Ascites</Label>
                  <Select
                    value={childPughData.ascites}
                    onValueChange={(value) => setChildPughData({ ...childPughData, ascites: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      <SelectItem value="mild">Mild</SelectItem>
                      <SelectItem value="moderate_severe">Moderate/Severe</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="col-span-2">
                  <Label>Hepatic Encephalopathy</Label>
                  <Select
                    value={childPughData.encephalopathy}
                    onValueChange={(value) => setChildPughData({ ...childPughData, encephalopathy: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      <SelectItem value="grade_1_2">Grade I-II</SelectItem>
                      <SelectItem value="grade_3_4">Grade III-IV</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button onClick={calculateChildPugh} className="w-full">
                <Calculator className="mr-2 h-4 w-4" />
                Calculate Child-Pugh Score
              </Button>

              {childPughResult && (
                <Alert>
                  <AlertDescription>
                    <div className="flex justify-between items-start">
                      <div className="space-y-1">
                        <div className="text-2xl font-bold">
                          {childPughResult.value}
                        </div>
                        <div className="text-sm">{childPughResult.interpretation}</div>
                        <div className="text-xs text-muted-foreground">{childPughResult.reference}</div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyResult(childPughResult)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}