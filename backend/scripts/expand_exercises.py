"""Expand exercise catalog to 80+ exercises."""
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

exercises_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'data', 'exercises.json')

with open(exercises_path, 'r') as f:
    existing = json.load(f)

base = 'https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises'

new_exercises = [
    # CHEST
    {'id':'cable-crossover','name':'Cable Crossover','category':'strength','primary_muscles':['chest'],'secondary_muscles':['shoulders'],'equipment':'cables','mechanic':'isolation','instructions':['Set pulleys to shoulder height.','Step forward and bring hands together.','Control the stretch on the way back.'],'gif_url':f'{base}/Cable_Crossover/0.jpg','axial_loading_rating':1},
    {'id':'decline-bench-press','name':'Barbell Decline Bench Press','category':'strength','primary_muscles':['chest'],'secondary_muscles':['triceps','shoulders'],'equipment':'barbell','mechanic':'compound','instructions':['Set bench to decline position.','Lower to lower chest and press up.'],'gif_url':f'{base}/Barbell_Bench_Press_-_Medium_Grip/0.jpg','axial_loading_rating':2},
    {'id':'dumbbell-pullover','name':'Dumbbell Pullover','category':'strength','primary_muscles':['chest','lats'],'secondary_muscles':['triceps'],'equipment':'dumbbells','mechanic':'compound','instructions':['Lie across bench holding dumbbell.','Lower behind head in an arc.','Pull back over chest.'],'gif_url':f'{base}/Dumbbell_Pullover/0.jpg','axial_loading_rating':1},
    {'id':'chest-dips','name':'Chest Dips','category':'strength','primary_muscles':['chest'],'secondary_muscles':['triceps','shoulders'],'equipment':'bodyweight','mechanic':'compound','instructions':['Lean forward on parallel bars.','Lower until shoulders below elbows.','Press back up.'],'gif_url':f'{base}/Dips/0.jpg','axial_loading_rating':1},
    {'id':'incline-barbell-press','name':'Incline Barbell Bench Press','category':'strength','primary_muscles':['chest'],'secondary_muscles':['shoulders','triceps'],'equipment':'barbell','mechanic':'compound','instructions':['Set bench to 30-45 degree incline.','Lower to upper chest and press.'],'gif_url':f'{base}/Incline_Barbell_Bench_Press/0.jpg','axial_loading_rating':3},
    {'id':'diamond-pushups','name':'Diamond Push-Up','category':'strength','primary_muscles':['chest','triceps'],'secondary_muscles':['core'],'equipment':'bodyweight','mechanic':'compound','instructions':['Place hands together forming a diamond.','Lower chest toward hands.','Push back up.'],'gif_url':f'{base}/Close-Grip_Push-Up/0.jpg','axial_loading_rating':1},
    # BACK
    {'id':'barbell-deadlift','name':'Barbell Deadlift','category':'strength','primary_muscles':['back','glutes'],'secondary_muscles':['hamstrings','lower_back','forearms'],'equipment':'barbell','mechanic':'compound','instructions':['Stand with feet hip-width.','Hinge at hips, grip bar.','Drive through heels.'],'gif_url':f'{base}/Deadlift/0.jpg','axial_loading_rating':5},
    {'id':'t-bar-row','name':'T-Bar Row','category':'strength','primary_muscles':['back','lats'],'secondary_muscles':['biceps','lower_back'],'equipment':'barbell','mechanic':'compound','instructions':['Straddle T-bar station.','Pull toward chest.','Squeeze shoulder blades.'],'gif_url':f'{base}/T-Bar_Row/0.jpg','axial_loading_rating':3},
    {'id':'seated-cable-row','name':'Seated Cable Row','category':'strength','primary_muscles':['back','lats'],'secondary_muscles':['biceps'],'equipment':'cables','mechanic':'compound','instructions':['Pull handle toward lower abdomen.','Squeeze shoulder blades.'],'gif_url':f'{base}/Seated_Cable_Row/0.jpg','axial_loading_rating':1},
    {'id':'straight-arm-pulldown','name':'Straight-Arm Pulldown','category':'strength','primary_muscles':['lats'],'secondary_muscles':['chest','triceps'],'equipment':'cables','mechanic':'isolation','instructions':['Pull bar down to thighs with straight arms.','Control back to start.'],'gif_url':f'{base}/Straight_Arm_Pulldown/0.jpg','axial_loading_rating':1},
    {'id':'chin-ups','name':'Chin-Ups','category':'strength','primary_muscles':['back','biceps'],'secondary_muscles':['forearms'],'equipment':'bodyweight','mechanic':'compound','instructions':['Underhand grip at shoulder width.','Pull chin above bar.','Lower with control.'],'gif_url':f'{base}/Chin-Ups/0.jpg','axial_loading_rating':1},
    {'id':'chest-supported-row','name':'Chest Supported Row','category':'strength','primary_muscles':['back','lats'],'secondary_muscles':['biceps'],'equipment':'dumbbells','mechanic':'compound','instructions':['Lie face down on incline bench.','Row dumbbells toward hips.'],'gif_url':f'{base}/One-Arm_Dumbbell_Row/0.jpg','axial_loading_rating':1},
    # LEGS
    {'id':'leg-press','name':'Leg Press','category':'strength','primary_muscles':['quads','glutes'],'secondary_muscles':['hamstrings'],'equipment':'bodyweight','mechanic':'compound','instructions':['Push platform away extending legs.','Lower under control.'],'gif_url':f'{base}/Leg_Press/0.jpg','axial_loading_rating':2},
    {'id':'leg-extension','name':'Leg Extension','category':'strength','primary_muscles':['quads'],'secondary_muscles':[],'equipment':'bodyweight','mechanic':'isolation','instructions':['Extend legs until straight.','Lower slowly.'],'gif_url':f'{base}/Leg_Extension/0.jpg','axial_loading_rating':1},
    {'id':'leg-curl','name':'Lying Leg Curl','category':'strength','primary_muscles':['hamstrings'],'secondary_muscles':['calves'],'equipment':'bodyweight','mechanic':'isolation','instructions':['Curl heels toward glutes.','Lower slowly.'],'gif_url':f'{base}/Lying_Leg_Curls/0.jpg','axial_loading_rating':1},
    {'id':'barbell-lunge','name':'Barbell Walking Lunge','category':'strength','primary_muscles':['quads','glutes'],'secondary_muscles':['hamstrings'],'equipment':'barbell','mechanic':'compound','instructions':['Step forward into deep lunge.','Drive through front heel.'],'gif_url':f'{base}/Barbell_Lunge/0.jpg','axial_loading_rating':3},
    {'id':'bulgarian-split-squat','name':'Bulgarian Split Squat','category':'strength','primary_muscles':['quads','glutes'],'secondary_muscles':['hamstrings'],'equipment':'dumbbells','mechanic':'compound','instructions':['Rear foot on bench.','Squat down with front leg.'],'gif_url':f'{base}/Bulgarian_Split_Squat/0.jpg','axial_loading_rating':2},
    {'id':'hip-thrust','name':'Barbell Hip Thrust','category':'strength','primary_muscles':['glutes'],'secondary_muscles':['hamstrings','core'],'equipment':'barbell','mechanic':'compound','instructions':['Drive hips upward squeezing glutes.','Lower with control.'],'gif_url':f'{base}/Barbell_Hip_Thrust/0.jpg','axial_loading_rating':2},
    {'id':'calf-raise-standing','name':'Standing Calf Raise','category':'strength','primary_muscles':['calves'],'secondary_muscles':[],'equipment':'bodyweight','mechanic':'isolation','instructions':['Raise heels as high as possible.','Lower below parallel for stretch.'],'gif_url':f'{base}/Standing_Calf_Raise/0.jpg','axial_loading_rating':1},
    {'id':'seated-calf-raise','name':'Seated Calf Raise','category':'strength','primary_muscles':['calves'],'secondary_muscles':[],'equipment':'bodyweight','mechanic':'isolation','instructions':['Raise heels extending ankles.','Lower slowly.'],'gif_url':f'{base}/Seated_Calf_Raise/0.jpg','axial_loading_rating':1},
    {'id':'front-squat','name':'Barbell Front Squat','category':'strength','primary_muscles':['quads','core'],'secondary_muscles':['glutes','upper_back'],'equipment':'barbell','mechanic':'compound','instructions':['Rest bar across front deltoids.','Squat keeping torso upright.'],'gif_url':f'{base}/Front_Squat/0.jpg','axial_loading_rating':5},
    {'id':'pistol-squat','name':'Pistol Squat','category':'strength','primary_muscles':['quads','glutes'],'secondary_muscles':['hamstrings','core'],'equipment':'bodyweight','mechanic':'compound','instructions':['Stand on one leg.','Squat down and drive back up.'],'gif_url':f'{base}/Pistol_Squat/0.jpg','axial_loading_rating':2},
    # SHOULDERS
    {'id':'face-pull','name':'Cable Face Pull','category':'strength','primary_muscles':['rear_delts','shoulders'],'secondary_muscles':['biceps','traps'],'equipment':'cables','mechanic':'isolation','instructions':['Pull rope toward face spreading elbows wide.','Squeeze rear delts.'],'gif_url':f'{base}/Face_Pull/0.jpg','axial_loading_rating':1},
    {'id':'arnold-press','name':'Arnold Press','category':'strength','primary_muscles':['shoulders'],'secondary_muscles':['triceps'],'equipment':'dumbbells','mechanic':'compound','instructions':['Hold at chin, press up rotating palms outward.'],'gif_url':f'{base}/Arnold_Dumbbell_Press/0.jpg','axial_loading_rating':2},
    {'id':'upright-row','name':'Dumbbell Upright Row','category':'strength','primary_muscles':['shoulders','traps'],'secondary_muscles':['biceps'],'equipment':'dumbbells','mechanic':'compound','instructions':['Pull elbows high and out to sides.'],'gif_url':f'{base}/Dumbbell_Upright_Row/0.jpg','axial_loading_rating':2},
    {'id':'rear-delt-fly','name':'Rear Delt Fly','category':'strength','primary_muscles':['rear_delts','shoulders'],'secondary_muscles':['traps'],'equipment':'dumbbells','mechanic':'isolation','instructions':['Bend forward, raise dumbbells out to sides.'],'gif_url':f'{base}/Rear_Delt_Fly/0.jpg','axial_loading_rating':1},
    {'id':'cable-lateral-raise','name':'Cable Lateral Raise','category':'strength','primary_muscles':['shoulders'],'secondary_muscles':[],'equipment':'cables','mechanic':'isolation','instructions':['Raise arm out to shoulder height.'],'gif_url':f'{base}/Cable_Lateral_Raise/0.jpg','axial_loading_rating':1},
    # ARMS
    {'id':'hammer-curl','name':'Dumbbell Hammer Curl','category':'strength','primary_muscles':['biceps','forearms'],'secondary_muscles':[],'equipment':'dumbbells','mechanic':'isolation','instructions':['Curl with neutral grip.'],'gif_url':f'{base}/Hammer_Curls/0.jpg','axial_loading_rating':1},
    {'id':'preacher-curl','name':'Barbell Preacher Curl','category':'strength','primary_muscles':['biceps'],'secondary_muscles':['forearms'],'equipment':'barbell','mechanic':'isolation','instructions':['Curl bar on preacher bench.'],'gif_url':f'{base}/Barbell_Curl/0.jpg','axial_loading_rating':1},
    {'id':'concentration-curl','name':'Concentration Curl','category':'strength','primary_muscles':['biceps'],'secondary_muscles':[],'equipment':'dumbbells','mechanic':'isolation','instructions':['Curl dumbbell with elbow against thigh.'],'gif_url':f'{base}/Concentration_Dumbbell_Curl/0.jpg','axial_loading_rating':1},
    {'id':'tricep-kickback','name':'Dumbbell Tricep Kickback','category':'strength','primary_muscles':['triceps'],'secondary_muscles':[],'equipment':'dumbbells','mechanic':'isolation','instructions':['Extend arm back straightening elbow.'],'gif_url':f'{base}/Dumbbell_Kickback/0.jpg','axial_loading_rating':1},
    {'id':'skull-crushers-barbell','name':'Barbell Skull Crushers','category':'strength','primary_muscles':['triceps'],'secondary_muscles':[],'equipment':'barbell','mechanic':'isolation','instructions':['Lower bar toward forehead, extend back up.'],'gif_url':f'{base}/Lying_Triceps_Press/0.jpg','axial_loading_rating':1},
    {'id':'overhead-tricep-extension','name':'Overhead Tricep Extension','category':'strength','primary_muscles':['triceps'],'secondary_muscles':[],'equipment':'dumbbells','mechanic':'isolation','instructions':['Lower dumbbell behind head, extend back up.'],'gif_url':f'{base}/Standing_Dumbbell_Triceps_Extension/0.jpg','axial_loading_rating':1},
    # CORE
    {'id':'russian-twist','name':'Russian Twist','category':'strength','primary_muscles':['core'],'secondary_muscles':['hip_flexors'],'equipment':'bodyweight','mechanic':'isolation','instructions':['Rotate torso side to side.'],'gif_url':f'{base}/Russian_Twist/0.jpg','axial_loading_rating':1},
    {'id':'ab-rollout','name':'Ab Rollout','category':'strength','primary_muscles':['core'],'secondary_muscles':['shoulders'],'equipment':'bodyweight','mechanic':'compound','instructions':['Roll forward extending body, pull back.'],'gif_url':f'{base}/Ab_Rollout/0.jpg','axial_loading_rating':1},
    {'id':'bicycle-crunch','name':'Bicycle Crunch','category':'strength','primary_muscles':['core'],'secondary_muscles':['hip_flexors'],'equipment':'bodyweight','mechanic':'isolation','instructions':['Alternate elbow to opposite knee.'],'gif_url':f'{base}/Bicycle_Crunch/0.jpg','axial_loading_rating':1},
    {'id':'dead-bug','name':'Dead Bug','category':'strength','primary_muscles':['core'],'secondary_muscles':[],'equipment':'bodyweight','mechanic':'isolation','instructions':['Extend opposite arm and leg.'],'gif_url':f'{base}/Dead_Bug/0.jpg','axial_loading_rating':1},
    {'id':'pallof-press','name':'Pallof Press','category':'strength','primary_muscles':['core'],'secondary_muscles':[],'equipment':'cables','mechanic':'isolation','instructions':['Press handle out, resist rotation.'],'gif_url':f'{base}/Pallof_Press/0.jpg','axial_loading_rating':1},
    {'id':'side-plank','name':'Side Plank','category':'strength','primary_muscles':['core'],'secondary_muscles':['shoulders','glutes'],'equipment':'bodyweight','mechanic':'isolation','instructions':['Lift hips forming straight line.'],'gif_url':f'{base}/Side_Plank/0.jpg','axial_loading_rating':1},
    {'id':'cable-crunch','name':'Cable Crunch','category':'strength','primary_muscles':['core'],'secondary_muscles':[],'equipment':'cables','mechanic':'isolation','instructions':['Crunch down bringing elbows to knees.'],'gif_url':f'{base}/Cable_Crunch/0.jpg','axial_loading_rating':1},
    {'id':'toes-to-bar','name':'Toes to Bar','category':'strength','primary_muscles':['core','hip_flexors'],'secondary_muscles':['forearms'],'equipment':'bodyweight','mechanic':'compound','instructions':['Raise legs until toes touch bar.'],'gif_url':f'{base}/Hanging_Leg_Raise/0.jpg','axial_loading_rating':1},
    # CARDIO
    {'id':'jump-rope','name':'Jump Rope','category':'cardio','primary_muscles':['cardio','calves'],'secondary_muscles':['shoulders'],'equipment':'bodyweight','mechanic':'compound','instructions':['Swing rope overhead and jump.'],'gif_url':f'{base}/Jump_Rope/0.jpg','axial_loading_rating':1},
    {'id':'burpees','name':'Burpees','category':'cardio','primary_muscles':['cardio','core'],'secondary_muscles':['chest','quads'],'equipment':'bodyweight','mechanic':'compound','instructions':['Squat, jump to plank, jump up.'],'gif_url':f'{base}/Burpees/0.jpg','axial_loading_rating':1},
    {'id':'mountain-climbers','name':'Mountain Climbers','category':'cardio','primary_muscles':['core','cardio'],'secondary_muscles':['shoulders'],'equipment':'bodyweight','mechanic':'compound','instructions':['Drive knees toward chest alternately.'],'gif_url':f'{base}/Mountain_Climbers/0.jpg','axial_loading_rating':1},
    {'id':'jumping-jacks','name':'Jumping Jacks','category':'cardio','primary_muscles':['cardio'],'secondary_muscles':['shoulders','calves'],'equipment':'bodyweight','mechanic':'compound','instructions':['Jump feet wide raising arms overhead.'],'gif_url':f'{base}/Jumping_Jacks/0.jpg','axial_loading_rating':1},
    {'id':'high-knees','name':'High Knees','category':'cardio','primary_muscles':['cardio','hip_flexors'],'secondary_muscles':['quads'],'equipment':'bodyweight','mechanic':'compound','instructions':['Run in place driving knees high.'],'gif_url':f'{base}/High_Knees/0.jpg','axial_loading_rating':1},
    # STRETCHING
    {'id':'pigeon-stretch','name':'Pigeon Stretch','category':'stretching','primary_muscles':['glutes','hip_flexors'],'secondary_muscles':[],'equipment':'bodyweight','mechanic':'isolation','instructions':['Bring knee forward to floor, extend back leg.'],'gif_url':f'{base}/Pigeon_Pose/0.jpg','axial_loading_rating':1},
    {'id':'hip-flexor-stretch','name':'Kneeling Hip Flexor Stretch','category':'stretching','primary_muscles':['hip_flexors','quads'],'secondary_muscles':[],'equipment':'bodyweight','mechanic':'isolation','instructions':['Push hips forward feeling stretch.'],'gif_url':f'{base}/Kneeling_Hip_Flexor/0.jpg','axial_loading_rating':1},
    {'id':'child-pose','name':'Child Pose','category':'stretching','primary_muscles':['lower_back','lats'],'secondary_muscles':['shoulders'],'equipment':'bodyweight','mechanic':'isolation','instructions':['Kneel and sit back on heels, extend arms forward.'],'gif_url':f'{base}/Child_Pose/0.jpg','axial_loading_rating':1},
    {'id':'hamstring-stretch','name':'Standing Hamstring Stretch','category':'stretching','primary_muscles':['hamstrings'],'secondary_muscles':['calves'],'equipment':'bodyweight','mechanic':'isolation','instructions':['Place heel on elevated surface, lean forward.'],'gif_url':f'{base}/Standing_Hamstring_Stretch/0.jpg','axial_loading_rating':1},
    {'id':'thoracic-rotation','name':'Thoracic Spine Rotation','category':'stretching','primary_muscles':['thoracic_spine','core'],'secondary_muscles':[],'equipment':'bodyweight','mechanic':'isolation','instructions':['Rotate top arm open like a book.'],'gif_url':f'{base}/Cat_Cow/0.jpg','axial_loading_rating':1},
    {'id':'foam-rolling-back','name':'Foam Rolling Upper Back','category':'stretching','primary_muscles':['upper_back','thoracic_spine'],'secondary_muscles':[],'equipment':'bodyweight','mechanic':'isolation','instructions':['Roll foam roller up and down upper back.'],'gif_url':f'{base}/Foam_Rolling/0.jpg','axial_loading_rating':1},
]

all_exercises = existing + new_exercises

with open(exercises_path, 'w', encoding='utf-8') as f:
    json.dump(all_exercises, f, indent=2, ensure_ascii=False)

print(f'Exercise catalog expanded: {len(existing)} -> {len(all_exercises)} exercises')
muscles = set()
for e in all_exercises:
    for m in e.get('primary_muscles', []):
        muscles.add(m)
print(f'Muscle groups: {len(muscles)}: {sorted(muscles)}')
eqs = set(e.get('equipment', '') for e in all_exercises)
print(f'Equipment: {sorted(eqs)}')
