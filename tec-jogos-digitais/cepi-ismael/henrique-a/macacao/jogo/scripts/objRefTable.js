const C3 = self.C3;
self.C3_GetObjectRefTable = function () {
	return [
		C3.Plugins.Sprite,
		C3.Behaviors.solid,
		C3.Behaviors.Platform,
		C3.Behaviors.scrollto,
		C3.Plugins.Keyboard,
		C3.Behaviors.Pin,
		C3.Plugins.System.Cnds.OnLayoutStart,
		C3.Plugins.Sprite.Acts.SetPos,
		C3.Plugins.Sprite.Exps.X,
		C3.Plugins.Sprite.Exps.Y,
		C3.Behaviors.Pin.Acts.PinByProperties,
		C3.Plugins.System.Cnds.IsGroupActive,
		C3.Plugins.Keyboard.Cnds.IsKeyDown,
		C3.Behaviors.Platform.Acts.SimulateControl,
		C3.Plugins.Sprite.Acts.SetMirrored,
		C3.Plugins.Keyboard.Cnds.OnKey,
		C3.Behaviors.Platform.Cnds.IsMoving,
		C3.Plugins.Sprite.Acts.SetAnim,
		C3.Behaviors.Platform.Cnds.IsJumping,
		C3.Behaviors.Platform.Cnds.OnStop,
		C3.Behaviors.Platform.Cnds.OnLand,
		C3.Plugins.Sprite.Cnds.OnCollision,
		C3.Plugins.Sprite.Acts.SetVisible
	];
};
self.C3_JsPropNameTable = [
	{ceu: 0},
	{Sólido: 0},
	{chao1: 0},
	{Plataforma: 0},
	{CentrarEm: 0},
	{jogadorsensor: 0},
	{Teclado: 0},
	{Fixar: 0},
	{macaco: 0},
	{Sprite: 0}
];

self.InstanceType = {
	ceu: class extends self.ISpriteInstance {},
	chao1: class extends self.ISpriteInstance {},
	jogadorsensor: class extends self.ISpriteInstance {},
	Teclado: class extends self.IInstance {},
	macaco: class extends self.ISpriteInstance {},
	Sprite: class extends self.ISpriteInstance {}
}